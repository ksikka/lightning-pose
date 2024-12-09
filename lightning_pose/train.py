"""Example model training function."""
import copy
import os
import random
import shutil
import sys
import warnings
from pathlib import Path

import lightning.pytorch as pl
import numpy as np
import torch
from omegaconf import DictConfig, ListConfig, OmegaConf, open_dict
from typeguard import typechecked

from lightning_pose.utils import pretty_print_cfg, pretty_print_str
from lightning_pose.utils import cropzoom
from lightning_pose.utils.io import (
    check_video_paths,
    ckpt_path_from_base_path,
    return_absolute_data_paths,
    return_absolute_path,
)
from lightning_pose.utils.predictions import (
    export_predictions_and_labeled_video,
    load_model_from_checkpoint,
    predict_dataset,
)
from lightning_pose.utils.scripts import (
    calculate_train_batches,
    compute_metrics,
    get_callbacks,
    get_data_module,
    get_data_module_pred,
    get_dataset,
    get_imgaug_transform,
    get_loss_factories,
    get_model,
)

# to ignore imports for sphix-autoapidoc
__all__ = ["train"]


class TrainingDataset:
    def __init__(self, cfg):
        self._model_cfg = cfg

    def has_ood_labels(self):
        cfg = self.cfg
        if isinstance(cfg.data.csv_file, list) or isinstance(cfg.data.csv_file, ListConfig):
            csv_file_ood = []
            for csv_file in cfg.data.csv_file:
                csv_file_ood.append(
                    os.path.join(cfg.data.data_dir, csv_file).replace(".csv", "_new.csv"))
        else:
            csv_file_ood = os.path.join(
                cfg.data.data_dir, cfg.data.csv_file).replace(".csv", "_new.csv")

        return (isinstance(csv_file_ood, str) and os.path.exists(csv_file_ood)) \
                or (isinstance(csv_file_ood, list) and os.path.exists(csv_file_ood[0]))


class Model:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.cfg = OmegaConf.load(model_dir / "config.yaml")
        self.training_dataset = TrainingDataset(self.cfg)

    def is_detector(self):
        return self.cfg.get("detector") is not None and self.cfg.detector.get("crop_ratio") is not None

@typechecked
def train(cfg: DictConfig) -> None:

    # reset all seeds
    seed = 0
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

    # record lightning-pose version
    from lightning_pose import __version__ as lightning_pose_version
    with open_dict(cfg):
        cfg.model.lightning_pose_version = lightning_pose_version

    # ----------------------------------------------------------------------------------
    # Save configuration in output directory
    # ----------------------------------------------------------------------------------
    # Done before training; files will exist even if script dies prematurely.
    hydra_output_directory = os.getcwd()
    print(f"Hydra output directory: {hydra_output_directory}")

    # save config file
    dest_config_file = Path(hydra_output_directory) / "config.yaml"
    OmegaConf.save(config=cfg, f=dest_config_file, resolve=True)
    print("Our Hydra config file:")
    pretty_print_cfg(cfg)
    

    # If detector_name is present, this is part of a cropzoom pipeline.
    @contextmanager
    def temporarily_make(var, temp_value):
        """
        A context manager that temporarily assigns a new value to a variable.

        Args:
            var: The variable to temporarily modify.
            temp_value: The temporary value to assign to the variable.
        """
        original_value = var
        try:
            var = temp_value
            yield
        finally:
            var = original_value

    if cfg.get("detector_name") is not None:
        detector_model = cropzoom.DetectorModel(cfg.detector_name)
        pose_model = cropzoom.PoseModel(Path(hydra_output_directory))
        # 1. Crop any data that detector didn't already crop (i.e. new labels or videos).
        cropzoom.predict_and_crop_any_new_labeled_frames(pose_model, detector_model)
        cropzoom.predict_and_crop_any_new_videos(pose_model, detector_model)
        
        # 2. Generate a csv_file in the cropped coordinate space.
        cropzoom.generate_cropped_csv_file(pose_model, detector_model)

        # 3. Rewrite config data_dir, video_dir, csv_file.
        cropped_cfg = pose_model.get_cropped_cfg()
    else:
        cropped_cfg = None
    data_dir, video_dir = return_absolute_data_paths(data_cfg=cfg.data)

    # ----------------------------------------------------------------------------------
    # Set up data/model objects
    # ----------------------------------------------------------------------------------

    # imgaug transform
    imgaug_transform = get_imgaug_transform(cfg=cfg)

    # dataset
    dataset = get_dataset(cfg=cfg, data_dir=data_dir, imgaug_transform=imgaug_transform)

    # datamodule; breaks up dataset into train/val/test
    data_module = get_data_module(cfg=cfg, dataset=dataset, video_dir=video_dir)

    # build loss factory which orchestrates different losses
    loss_factories = get_loss_factories(cfg=cfg, data_module=data_module)

    # model
    model = get_model(cfg=cfg, data_module=data_module, loss_factories=loss_factories)

    # save labeled data file(s)
    if isinstance(cfg.data.csv_file, str):
        # single view
        csv_files = [cfg.data.csv_file]
    else:
        # multi view
        assert isinstance(cfg.data.csv_file, ListConfig)
        csv_files = cfg.data.csv_file
    for csv_file in csv_files:
        src_csv_file = Path(csv_file)
        if not src_csv_file.is_absolute():
            src_csv_file = Path(data_dir) / src_csv_file

        dest_csv_file = Path(hydra_output_directory) / src_csv_file.name
        shutil.copyfile(src_csv_file, dest_csv_file)

    # ----------------------------------------------------------------------------------
    # Set up and run training
    # ----------------------------------------------------------------------------------

    # logger
    logger = pl.loggers.TensorBoardLogger("tb_logs", name=cfg.model.model_name)
    # Log hydra config to tensorboard as helpful metadata.
    for key, value in cfg.items():
        logger.experiment.add_text(
            "hydra_config_%s" % key, "```\n%s```" % OmegaConf.to_yaml(value)
        )

    # early stopping, learning rate monitoring, model checkpointing, backbone unfreezing
    callbacks = get_callbacks(
        cfg,
        early_stopping=cfg.training.get("early_stopping", False),
        lr_monitor=True,
        ckpt_every_n_epochs=cfg.training.get("ckpt_every_n_epochs", None)
    )

    # calculate number of batches for both labeled and unlabeled data per epoch
    limit_train_batches = calculate_train_batches(cfg, dataset)

    # set up trainer

    # Old configs may have num_gpus: 0. We will remove support in a future release.
    if cfg.training.num_gpus == 0:
        warnings.warn(
            "Config contains unsupported value num_gpus: 0. "
            "Update num_gpus to 1 in your config."
        )
    cfg.training.num_gpus = max(cfg.training.num_gpus, 1)

    trainer = pl.Trainer(
        accelerator="gpu",
        devices=cfg.training.num_gpus,
        max_epochs=cfg.training.max_epochs,
        min_epochs=cfg.training.min_epochs,
        check_val_every_n_epoch=min(
            cfg.training.check_val_every_n_epoch,
            cfg.training.max_epochs,  # for debugging or otherwise training for a short time
        ),
        log_every_n_steps=cfg.training.log_every_n_steps,
        callbacks=callbacks,
        logger=logger,
        limit_train_batches=limit_train_batches,
        accumulate_grad_batches=cfg.training.get("accumulate_grad_batches", 1),
        profiler=cfg.training.get("profiler", None),
        sync_batchnorm=True,
    )

    # train model!
    trainer.fit(model=model, datamodule=data_module)

    # When devices > 0, lightning creates a process per device.
    # Kill processes other than the main process, otherwise they all go forward.
    if not trainer.is_global_zero:
        sys.exit(0)
    
    return Model(Path(hydra_output_directory))


def predict_on_training_frames(model):
    # ----------------------------------------------------------------------------------
    # predict on all labeled frames (train/val/test)
    # ----------------------------------------------------------------------------------
    pretty_print_str("Predicting train/val/test images...")
    predict_dataset(model.cfg)

def compute_metrics_on_training_frame_predictions(model):
    cfg = model.cfg
    data_module_pred = get_data_module_pred(cfg=cfg)

    # compute and save various metrics
    # for multiview, predict_dataset outputs one pred file per view.
    multiview_pred_files = [
        str(Path(model.model_dir) / p)
        for p in Path(model.model_dir).glob("predictions_*.csv")
    ]
    if len(multiview_pred_files) > 0:
        preds_file = multiview_pred_files
    compute_metrics(cfg=cfg, preds_file=preds_file, data_module=data_module_pred)

    # TODO take out.
    
    if model.is_detector():
        cropzoom.generate_cropped_labeled_frames(
            root_directory=Path(cfg.data_dir),
            output_directory=Path(model.model_dir),
            detector_cfg=cfg.detector,
        )

def predict_on_test_videos(model):
    cfg = model.cfg
    data_module_pred = get_data_module_pred(cfg=cfg)
    # ----------------------------------------------------------------------------------
    # predict folder of videos
    # ----------------------------------------------------------------------------------

    pretty_print_str("Predicting videos...")
    if cfg.eval.test_videos_directory is None:
        filenames = []
    else:
        filenames = check_video_paths(return_absolute_path(cfg.eval.test_videos_directory))
        vidstr = "video" if (len(filenames) == 1) else "videos"
        pretty_print_str(
            f"Found {len(filenames)} {vidstr} to predict (in cfg.eval.test_videos_directory)"
        )

    for video_file in filenames:
        assert os.path.isfile(video_file)

        pretty_print_str(f"Predicting video: {video_file}...")
        # get save name for prediction csv file
        video_pred_dir = os.path.join(model.model_dir, "video_preds")
        video_pred_name = os.path.splitext(os.path.basename(video_file))[0]
        prediction_csv_file = os.path.join(video_pred_dir, video_pred_name + ".csv")
        # get save name labeled video csv
        if cfg.eval.save_vids_after_training:
            labeled_vid_dir = os.path.join(video_pred_dir, "labeled_videos")
            labeled_mp4_file = os.path.join(labeled_vid_dir, video_pred_name + "_labeled.mp4")
        else:
            labeled_mp4_file = None
        # predict on video
        export_predictions_and_labeled_video(
            video_file=video_file,
            cfg=cfg,
            prediction_csv_file=prediction_csv_file,
            labeled_mp4_file=labeled_mp4_file,
            data_module=data_module_pred,
            save_heatmaps=cfg.eval.get(
                "predict_vids_after_training_save_heatmaps", False
            ),
        )

def compute_metrics_on_test_videos(model):


    for video_file in filenames:
        prediction_csv_file = os.path.join(video_pred_dir, video_pred_name + ".csv")
        compute_metrics(
            cfg=cfg,
            preds_file=prediction_csv_file,
            data_module=data_module_pred,
        )

    for video_file in filenames:
        if model.is_detector():
            cropzoom.generate_cropped_video(
                video_path=Path(video_file),
                detector_model_dir=Path(model.model_dir),
                detector_cfg=cfg.detector,
            )
    
def predict_on_ood_frames(model):
    cfg = model.cfg
    _, video_dir = return_absolute_data_paths(cfg.data)
    # ----------------------------------------------------------------------------------
    # predict on OOD frames
    # ----------------------------------------------------------------------------------
    # update config file to point to OOD data
    cfg_ood = cfg.copy()
    cfg_ood.data.csv_file = csv_file_ood
    cfg_ood.training.imgaug = "default"
    cfg_ood.training.train_prob = 1
    cfg_ood.training.val_prob = 0
    cfg_ood.training.train_frames = 1
    # build dataset/datamodule
    imgaug_transform_ood = get_imgaug_transform(cfg=cfg_ood)
    dataset_ood = get_dataset(
        cfg=cfg_ood, data_dir=cfg.data.data_dir, imgaug_transform=imgaug_transform_ood
    )
    data_module_ood = get_data_module(cfg=cfg_ood, dataset=dataset_ood, video_dir=video_dir)
    data_module_ood.setup()
    pretty_print_str("Predicting OOD images...")
    # compute and save frame-wise predictions
    predict_dataset(
        cfg=cfg_ood,
        data_module=data_module_ood,
        preds_file_suffix="new",
    )

def predict_on_ood_frames(model):
    cfg = model.cfg
    # ----------------------------------------------------------------------------------
    # predict on OOD frames
    # ----------------------------------------------------------------------------------
    # update config file to point to OOD data
    cfg_ood = cfg.copy()
    cfg_ood.data.csv_file = csv_file_ood
    cfg_ood.training.imgaug = "default"
    cfg_ood.training.train_prob = 1
    cfg_ood.training.val_prob = 0
    cfg_ood.training.train_frames = 1
    # build dataset/datamodule
    imgaug_transform_ood = get_imgaug_transform(cfg=cfg_ood)
    dataset_ood = get_dataset(
        cfg=cfg_ood, data_dir=cfg.data.data_dir, imgaug_transform=imgaug_transform_ood
    )
    data_module_ood = get_data_module(cfg=cfg_ood, dataset=dataset_ood, video_dir=video_dir)
    data_module_ood.setup()
    
    # compute and save various metrics
    preds_file_ood = os.path.join(model.model_dir, "predictions_new.csv")
    # take care of multiview case, where multiple csv files have been saved
    preds_files = [
        os.path.join(model.model_dir, path) for path in
        os.listdir(model.model_dir) if path.startswith("predictions_new")
    ]
    if len(preds_files) > 1:
        preds_file_ood = preds_files
    compute_metrics(cfg=cfg_ood, preds_file=preds_file_ood, data_module=data_module_ood)

