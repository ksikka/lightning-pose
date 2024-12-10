import argparse
import os
import typing
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Predict on a directory of PNG files. "
        "Outputs to a directory named predict_frames_<frames_dir>."
    )
    parser.add_argument("model_dir", type=str, help="Path to the model directory.")
    parser.add_argument(
        "frames_dir", type=str, help="Path to a directory containing PNG files."
    )

    args = parser.parse_args()

    # Get the basename of the frames directory
    frames_dir_basename = os.path.basename(args.frames_dir)

    # Construct the output directory name
    output_dir = f"predict_frames_{frames_dir_basename}"
    os.makedirs(output_dir, exist_ok=True)

    predict_frames(args.model_dir, output_dir, args.frames_dir)


def predict_frames(
    model_dir: str,
    output_dir: str,
    frames_dir: str,
):
    # Lazy import to make argparse fail faster if args are invalid.
    import imgaug.augmenters as iaa
    import lightning.pytorch as pl
    import pandas as pd
    from omegaconf import DictConfig, OmegaConf
    from torch.utils.data import DataLoader

    from lightning_pose.models import ALLOWED_MODELS
    from lightning_pose.utils.io import ckpt_path_from_base_path
    from lightning_pose.utils.predictions import (
        PredictionHandler,
        load_model_from_checkpoint,
    )
    from lightning_pose.utils.scripts import (
        get_data_module,
        get_dataset,
        get_imgaug_transform,
    )

    cfg = OmegaConf.load(Path(model_dir) / "config.yaml")
    cfg = typing.cast(DictConfig, cfg)

    best_ckpt = ckpt_path_from_base_path(model_dir, cfg.model.model_name)
    model = load_model_from_checkpoint(
        cfg=cfg,
        ckpt_file=best_ckpt,
        eval=True,
        skip_data_module=True,
    )

    # Generate fake CSV file
    ls_output = os.listdir(frames_dir)
    # - Filter to image files
    ls_output = [x for x in ls_output if x.endswith(".png")]
    fake_csv_data = [[0] * 2 * len(cfg.data.keypoint_names) for _ in ls_output]
    columns = pd.MultiIndex.from_product(
        [["na"], cfg.data.keypoint_names, ["x", "y"]],
        names=["scorer", "bodyparts", "coords"],
    )
    df = pd.DataFrame(fake_csv_data, columns=columns, index=ls_output)
    csv_file = str((Path(output_dir) / ".CollectedData.csv").absolute())
    df.to_csv(csv_file)

    # Update config as required for inference.
    cfg.data.csv_file = csv_file
    # - Dataset will only use resize transform for inference.
    cfg.training.imgaug = "default"
    # - PredictionHandler requires data_module for:
    #     1. Getting access to the dataset.
    #     2. Getting the test/train/val split.
    cfg.training.train_prob = 1.0
    cfg.training.val_prob = 0.0
    cfg.training.train_frames = 1
    cfg.model.losses_to_use = []  # Make BaseDataModule.

    imgaug_transform = get_imgaug_transform(cfg)
    dataset = get_dataset(
        cfg=cfg,
        data_dir=frames_dir,
        imgaug_transform=imgaug_transform,
    )

    data_loader = DataLoader(
        dataset,
        batch_size=100,  # Depends on the available memory.
        num_workers=4,  # self.num_workers,
        persistent_workers=True,  # if self.num_workers > 0 else False,
    )
    trainer = pl.Trainer(devices=1, accelerator="auto")

    predictions = trainer.predict(
        model=model,
        dataloaders=data_loader,
    )

    data_module = get_data_module(cfg=cfg, dataset=dataset)
    data_module.setup()
    pred_handler = PredictionHandler(cfg=cfg, data_module=data_module)
    # call this instance on a single vid's preds
    preds_df = pred_handler(preds=predictions)
    pred_csv_path = Path(output_dir) / "predictions.csv"
    preds_df.to_csv(pred_csv_path)

    # filter columns to only x, y (drop likelihood and set)
    preds_df = preds_df.loc[:, preds_df.columns.get_level_values(2).isin(["x", "y"])]
    for img_path, series in preds_df.iterrows():
        # points = series.values.reshape(-1, 2)
        annotate_image_with_points(frames_dir, img_path, series.to_numpy(), output_dir)
    print("Predictions & Annotated images saved to:", output_dir)


def annotate_image_with_points(root_dir, image_path, points, output_dir):
    """
    Annotates an image with dots at specific points.

    Args:
        root_dir (str): Path to the directory containing image files.
        image_path (str): Path to the image file relative to root_dir.
        points (numpy.ndarray): A numpy array of x, y values representing the points.
                                 For example, for two points: x1, y1, x2, y2
        output_dir (str): Path to the output directory.
    """
    from PIL import Image, ImageDraw
    from matplotlib import cm

    # Load the image
    img = Image.open(os.path.join(root_dir, image_path))
    draw = ImageDraw.Draw(img)

    # Use a colormap to get consistent colors
    colormap = cm.get_cmap("tab20")  # You can choose any colormap you like

    # Reshape the points array for easier iteration
    points = points.reshape(-1, 2)

    # Draw dots on the image
    for i, (x, y) in enumerate(points):
        color = tuple(
            int(c * 255) for c in colormap(i)[:3]
        )  # Get RGB color from colormap
        draw.ellipse(
            (x - 2, y - 2, x + 2, y + 2), fill=color
        )  # Draw a dot with radius 2

    # Save the annotated image
    filename = os.path.basename(image_path)
    output_path = os.path.join(output_dir, filename)
    img.save(output_path)


if __name__ == "__main__":
    main()