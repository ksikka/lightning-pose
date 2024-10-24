"""Test the scripts module.

Note that many of the functions in the scripts module are explicitly used (and therefore implicitly
tested) in conftest.py

"""

import copy
import gc
import lightning.pytorch as pl
from omegaconf import OmegaConf
from omegaconf.errors import ValidationError
import os
import pytest
import torch
from unittest.mock import Mock

from lightning_pose.data.datasets import BaseTrackingDataset
from lightning_pose.utils.scripts import (
    calculate_train_batches,
    export_predictions_and_labeled_video,
    get_data_module,
    get_loss_factories,
    get_model,
)


def test_calculate_train_batches(cfg, base_dataset):
    """Test the computation of train batches, which is a function of labeled and unlabeled info."""
    cfg_tmp = copy.deepcopy(cfg)

    # return value if set in config
    for n in [2, 12, 22]:
        cfg_tmp.training.limit_train_batches = n
        n_batches = calculate_train_batches(cfg_tmp, base_dataset)
        assert n_batches == n

    # None with small number of train frames - return minimum of 10
    cfg_tmp.training.limit_train_batches = None
    cfg_tmp.training.train_frames = 2
    n_batches = calculate_train_batches(cfg_tmp, base_dataset)
    assert n_batches == 10

    # None with large number of frames
    n = 50
    cfg_tmp.training.limit_train_batches = None
    cfg_tmp.training.train_frames = n
    cfg_tmp.training.train_batch_size = 1
    n_batches = calculate_train_batches(cfg_tmp, base_dataset)
    assert n_batches == n


def test_export_predictions_and_labeled_video(
        cfg, heatmap_data_module, video_list, remove_logs, tmpdir):
    """Test helper function that predicts videos then makes a labeled movie."""
    # make a basic heatmap tracker
    cfg_tmp = copy.deepcopy(cfg)
    cfg_tmp.model.model_type = "heatmap"
    cfg_tmp.model.losses_to_use = []

    # build loss factory which orchestrates different losses
    loss_factories = get_loss_factories(cfg=cfg_tmp, data_module=heatmap_data_module)

    # build model
    model = get_model(cfg=cfg_tmp, data_module=heatmap_data_module, loss_factories=loss_factories)

    # make a checkpoint callback so we know where model is saved
    ckpt_callback = pl.callbacks.model_checkpoint.ModelCheckpoint(dirpath=str(tmpdir))

    # train model for a couple epochs
    trainer = pl.Trainer(
        accelerator="gpu",
        devices=1,
        max_epochs=2,
        min_epochs=2,
        check_val_every_n_epoch=1,
        log_every_n_steps=1,
        callbacks=[ckpt_callback],
        limit_train_batches=2,
    )
    trainer.fit(model=model, datamodule=heatmap_data_module)

    # test 1: all available inputs
    csv_file = str(tmpdir.join("test1.csv"))
    mp4_file = str(tmpdir.join("test1.mp4"))
    npy_file = csv_file.replace(".csv", "_heatmaps.npy")
    export_predictions_and_labeled_video(
        video_file=video_list[0],
        cfg=cfg_tmp,
        prediction_csv_file=csv_file,
        ckpt_file=None,
        trainer=trainer,
        model=model,
        data_module=heatmap_data_module,
        labeled_mp4_file=mp4_file,
        save_heatmaps=False,
    )
    assert os.path.exists(csv_file)
    assert os.path.exists(mp4_file)
    assert not os.path.exists(npy_file)

    # test 2: no trainer
    csv_file = str(tmpdir.join("test2.csv"))
    mp4_file = str(tmpdir.join("test2.mp4"))
    npy_file = csv_file.replace(".csv", "_heatmaps.npy")
    export_predictions_and_labeled_video(
        video_file=video_list[0],
        cfg=cfg_tmp,
        prediction_csv_file=csv_file,
        ckpt_file=None,
        trainer=None,
        model=model,
        data_module=heatmap_data_module,
        labeled_mp4_file=mp4_file,
        save_heatmaps=False,
    )
    assert os.path.exists(csv_file)
    assert os.path.exists(mp4_file)
    assert not os.path.exists(npy_file)

    # test 3: no trainer, no model, save heatmaps
    csv_file = str(tmpdir.join("test3.csv"))
    mp4_file = str(tmpdir.join("test3.mp4"))
    npy_file = csv_file.replace(".csv", "_heatmaps.npy")
    export_predictions_and_labeled_video(
        video_file=video_list[0],
        cfg=cfg_tmp,
        prediction_csv_file=csv_file,
        ckpt_file=ckpt_callback.best_model_path,
        trainer=None,
        model=None,
        data_module=heatmap_data_module,
        labeled_mp4_file=mp4_file,
        save_heatmaps=True,
    )
    assert os.path.exists(csv_file)
    assert os.path.exists(mp4_file)
    assert os.path.exists(npy_file)

    # test 4: raise proper error
    with pytest.raises(ValueError):
        export_predictions_and_labeled_video(
            video_file=video_list[0],
            cfg=cfg_tmp,
            prediction_csv_file=str(tmpdir.join("test4.csv")),
            ckpt_file=None,
            trainer=trainer,
            model=None,
            data_module=heatmap_data_module,
            labeled_mp4_file=str(tmpdir.join("test3.mp4")),
            save_heatmaps=False,
        )

    # remove tensors from gpu
    del loss_factories
    del model
    gc.collect()
    torch.cuda.empty_cache()

    # clean up logging
    remove_logs()


def _supervised_multi_gpu_cfg(cfg):
    return OmegaConf.merge(
        cfg,
        OmegaConf.create(
            {
                "model": {
                    "losses_to_use": [],
                },
                "training": {
                    "num_gpus": 2,
                    "train_batch_size": 4,
                    "val_batch_size": 16,
                    "test_batch_size": 16,
                },
            }
        ),
    )


def test_get_data_module_num_gpus_0(cfg):
    cfg = _supervised_multi_gpu_cfg(cfg)
    # when num_gpus is set to 0, i.e. from a deprecated config
    cfg.training.num_gpus = 0
    data_module = get_data_module(cfg, Mock(spec=BaseTrackingDataset))

    # assert num_gpus gets modified to 1
    assert cfg.training.num_gpus == 1
    # the rest of the behavior follows correctly
    assert data_module.train_batch_size == cfg.training.train_batch_size
    assert data_module.val_batch_size == cfg.training.val_batch_size
    assert data_module.test_batch_size == cfg.training.test_batch_size


def test_get_data_module_multi_gpu_batch_size_adjustment(cfg):
    cfg = _supervised_multi_gpu_cfg(cfg)
    data_module = get_data_module(cfg, Mock(spec=BaseTrackingDataset))
    # train, val batch sizes should be divided by num_gpus
    assert data_module.train_batch_size == cfg.training.train_batch_size / 2
    assert data_module.val_batch_size == cfg.training.val_batch_size / 2
    assert data_module.test_batch_size == cfg.training.test_batch_size


def test_get_data_module_train_batch_size_not_divisible_by_num_gpus(cfg):
    cfg = _supervised_multi_gpu_cfg(cfg)

    # When test_batch_size is indivisible by 2
    cfg.training.train_batch_size += 1
    with pytest.raises(ValidationError):
        get_data_module(cfg, Mock(spec=BaseTrackingDataset))


def test_get_data_module_val_batch_size_not_divisible_by_num_gpus(cfg):
    cfg = _supervised_multi_gpu_cfg(cfg)

    # When test_batch_size is indivisible by 2
    cfg.training.val_batch_size += 1
    with pytest.raises(ValidationError):
        get_data_module(cfg, Mock(spec=BaseTrackingDataset))


def test_get_data_module_multi_gpu_unsupervised_unsupported(cfg):
    # when the model has unsupervised losses and num_gpus > 1
    cfg = _supervised_multi_gpu_cfg(cfg)
    cfg.model.losses_to_use = ["pca_singleview"]

    with pytest.raises(ValidationError):
        get_data_module(cfg, Mock(spec=BaseTrackingDataset))
