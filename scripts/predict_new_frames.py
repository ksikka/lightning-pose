import argparse

from omegaconf import OmegaConf
from pathlib import Path
from lightning_pose.utils import pretty_print_str

def main():
    r"""
    Predicts new frames using a trained model.
    
    Example: python scripts/predict_new_frames.py \
        --model_dir outputs/pr-sup-heatmap-singleview-1gpu/21-51-47 \
        --data_dir=data/mirror-mouse/ \
        --labels_file data/mirror-mouse/CollectedData_new.csv \
        --predictions_file outputs/ood_preds/test_out.csv
    """

    parser = argparse.ArgumentParser(description="Predict new frames using a trained model.")
    parser.add_argument("--model_dir", required=True, type=Path, help="Model directory.")
    parser.add_argument("--data_dir", type=Path, required=True, help="Data directory.")
    parser.add_argument("--labels_file", type=Path, required=True, help="Label file.")
    parser.add_argument("--predictions_file", type=Path, required=True, help="Output file.")
    args = parser.parse_args()

    # Access the arguments
    model_dir = args.model_dir
    data_dir = args.data_dir
    labels_file = args.labels_file
    predictions_file = args.predictions_file

    # TODO: validate files and folders.

    cfg = OmegaConf.load(model_dir / "config.yaml")

    cfg.training.imgaug = "default"
    cfg.data.data_dir = data_dir
    cfg.data.csv_file = labels_file
    # No need to trigger unsupervised datamodule.
    # predict_dataset will use full_labeled_dataloader().
    cfg.model.losses_to_use = []

    import lightning.pytorch as pl
    
    from lightning_pose.utils.io import (
        ckpt_path_from_base_path,
    )
    from lightning_pose.utils.predictions import load_model_from_checkpoint, predict_dataset
    ckpt_file = ckpt_path_from_base_path(
        base_path=model_dir, model_name=cfg.model.model_name
    )
    from lightning_pose.utils.scripts import (
        get_data_module,
        get_dataset,
        get_imgaug_transform,
    )
    model = load_model_from_checkpoint(
        cfg=cfg,
        ckpt_file=ckpt_file,
        eval=True,
        skip_data_module=True
    )
    trainer = pl.Trainer(accelerator="gpu", devices=1)
    pretty_print_str("Predicting images...")

    print("getting imgaug transform...")
    imgaug_transform = get_imgaug_transform(cfg=cfg)
    print("getting dataset...")
    dataset = get_dataset(cfg=cfg, data_dir=data_dir, imgaug_transform=imgaug_transform)
    
    assert dataset is not None

    # TODO Get rid of datamodule requirement of predict_dataset.
    print("getting data module...")
    data_module = get_data_module(cfg=cfg, dataset=dataset)
    data_module.setup()

    predict_dataset(
        cfg=cfg,
        trainer=trainer,
        model=model,
        data_module=data_module,
        preds_file=predictions_file,
    )

    print(f"Outputted to {predictions_file}")

if __name__ == "__main__":
    main()