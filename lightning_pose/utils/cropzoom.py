import copy
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from moviepy.editor import VideoFileClip
from omegaconf import DictConfig
from PIL import Image
from typeguard import typechecked
from omegaconf import OmegaConf

from lightning_pose.utils.io import get_context_img_paths

__all__ = ["generate_cropped_labeled_frames", "generate_cropped_video"]


@typechecked
def _calculate_bbox_size(
    keypoints_per_frame: np.ndarray, crop_ratio: float = 1.0
) -> int:
    """Given all labeled keypoints, computes the bounding box square size as
    the length of one side in pixels.
    First we compute the maximum bounding box that would always encompass
    the animal (maximum difference of all x's and y's per frame, max over all frames).
    Then we take the larger dimension of the bbox (x or y). Finally we scale by `crop_ratio`.

    Arguments:
        keypoints_per_frame: np array of all labeled frames. Shape of (frames, keypoints, x|y).
        crop_ratio:
    """
    # Extract x and y coordinates
    x_coords = keypoints_per_frame[:, :, 0]  # All rows, all columns, first element (x)
    y_coords = keypoints_per_frame[:, :, 1]  # All rows, all columns, second element (y)
    max_x_diff_per_frame = np.max(x_coords, axis=1) - np.min(x_coords, axis=1)
    max_y_diff_per_frame = np.max(y_coords, axis=1) - np.min(y_coords, axis=1)

    # Max of all x_diff and y_diff over all frames. A scalar.
    max_bbox_size = np.max([max_x_diff_per_frame, max_y_diff_per_frame], axis=(0, 1))

    # Scale by crop_ratio, and take ceiling.
    bbox_size = int(np.ceil(max_bbox_size * crop_ratio))

    # Many video players don't like odd dimensions.
    # Make sure the bbox has even dimensions.
    bbox_size = bbox_size if bbox_size % 2 == 0 else bbox_size + 1

    return bbox_size


@typechecked
def _compute_bbox_df(
    pred_df: pd.DataFrame, anchor_keypoints: List[str], crop_ratio: float = 1.0
) -> pd.DataFrame:
    # Get x,y columns for anchor_keypoints (or all keypoints if anchor_keypoints is empty)
    coord_mask = pred_df.columns.get_level_values("coords").isin(["x", "y"])
    if len(anchor_keypoints) > 0:
        coord_mask &= pred_df.columns.get_level_values("bodyparts").isin(
            anchor_keypoints
        )

    # Shape: (frames, keypoints, x|y)
    keypoints_per_frame = (
        pred_df.loc[:, coord_mask].to_numpy().reshape(pred_df.shape[0], -1, 2)
    )

    bbox_size = _calculate_bbox_size(keypoints_per_frame, crop_ratio=crop_ratio)

    # Shape: (frames, keypoints, x|y) -> (frames, x|y)
    centroids = keypoints_per_frame.mean(axis=1)

    # Instead of storing centroid, we'll store bbox top-left.
    # Shape: (frames, x|y)
    bbox_toplefts = centroids - bbox_size // 2
    # Floor and store ints.
    bbox_toplefts = np.int64(bbox_toplefts)

    # Store bbox size as (h,w). Note that h=w since bbox is a square for now.
    # Shape: (frames, h|w)
    bbox_hws = np.full_like(bbox_toplefts, bbox_size)

    # Shape: (frames, x|y) -> (frames, x|y|h|w)
    bboxes = np.concatenate([bbox_toplefts, bbox_hws], axis=1)

    index = pred_df.index

    return pd.DataFrame(bboxes, index=index, columns=["x", "y", "h", "w"])


@typechecked
def _crop_images(
    bbox_df: pd.DataFrame, root_directory: Path, output_directory: Path
) -> None:
    """Crops images according to their bboxes in `bbox_df`.

    root_directory: root of img paths in bbox_df.
    output_directory: where to save cropped images."""
    for center_img_path, row in bbox_df.iterrows():
        for img_path in get_context_img_paths(Path(center_img_path)):
            # Silently skip non-existent context frames.
            if not (root_directory / img_path).exists() and img_path != center_img_path:
                continue
            img = Image.open(root_directory / img_path)
            img = img.crop((row.x, row.y, row.x + row.h, row.y + row.w))

            # preserve directory structure of img_path
            # (e.g. labeled-data/x.png will create a labeled-data dir)
            cropped_img_path = output_directory / img_path
            cropped_img_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(cropped_img_path)


@typechecked
def _crop_video_moviepy(
    video_file: Path, bbox_df: pd.DataFrame, output_directory: Path
):
    clip = VideoFileClip(str(video_file))

    b = bbox_df.iloc[0]
    h = b.h
    w = b.w

    def crop_frame(get_frame, t):
        frame = get_frame(t)

        frame_index = int(t * clip.fps)  # Calculate frame index based on time
        if frame_index >= len(bbox_df):
            print(f"crop_frame: Skipped frame {frame_index}")
            return np.zeros((h, w, frame.shape[2]), dtype=np.uint8)

        b = bbox_df.iloc[frame_index]
        x1, x2 = b.x, b.x + b.w
        y1, y2 = b.y, b.y + b.h
        assert b.h == h
        assert b.w == w
        cropped_frame = np.zeros((h, w, frame.shape[2]), dtype=np.uint8)

        # Calculate valid crop boundaries within the original frame
        x1_valid = max(0, x1)
        x2_valid = min(clip.w - 1, x2)
        y1_valid = max(0, y1)
        y2_valid = min(clip.h - 1, y2)

        # Calculate corresponding coordinates in the cropped frame
        crop_x1 = abs(min(0, x1))  # Offset in the cropped frame if x1 is negative
        crop_x2 = crop_x1 + (x2_valid - x1_valid)
        crop_y1 = abs(min(0, y1))  # Offset in the cropped frame if y1 is negative
        crop_y2 = crop_y1 + (y2_valid - y1_valid)

        # Copy the valid region to the cropped frame
        cropped_frame[crop_y1:crop_y2, crop_x1:crop_x2] = frame[
            y1_valid:y2_valid, x1_valid:x2_valid
        ]

        return cropped_frame

    # renamed image_transform in 2.0.0
    cropped_clip = clip.fl(crop_frame, apply_to="mask")

    cropped_clip.write_videofile(
        str(output_directory / video_file.name), codec="libx264"
    )


@typechecked
def generate_cropped_labeled_frames(
    root_directory: Path,
    output_directory: Path,
    detector_cfg: DictConfig,
    preds_file: Optional[Path] = None,
) -> None:
    # Use predictions rather than CollectedData.csv because collected data can sometimes have NaNs.
    preds_file = preds_file or output_directory / "predictions.csv"
    # load predictions
    pred_df = pd.read_csv(preds_file, header=[0, 1, 2], index_col=0)

    # compute and save bbox_df
    bbox_df = _compute_bbox_df(
        pred_df, list(detector_cfg.anchor_keypoints), crop_ratio=detector_cfg.crop_ratio
    )

    bbox_csv_path = output_directory / "cropped_images" / "bbox.csv"
    bbox_csv_path.parent.mkdir(parents=True, exist_ok=True)
    bbox_df.to_csv(bbox_csv_path)

    _crop_images(bbox_df, root_directory, output_directory / "cropped_images")

def predict_and_crop_any_new_labeled_frames(pose_model, detector_model):
    # Not yet implemented.
    # find the frames referenced by pose_model's labeled dataset that are not yet cropped.
    #   load CollectedData.csv into a pd.DataFrame
    #   load detector's bbox.csv into a pd.DataFrame
    #   subtract the two to get a list of image paths that need cropping.
    # run detector prediction on them (=> pred_df)
    # then call:
    
    # generate_cropped_labeled_frames(
    #     root_directory=pose_model.cfg.data.data_dir,
    #     output_directory=detector_model.get_cropped_data_dir(),
    #     detector_cfg=detector_model.cfg,
    #     pred_df=pred_df)
    pass

def predict_and_crop_any_new_videos(pose_model, detector_model):
    # Not yet implemented.
    # find the videos that are not yet cropped.
    #   get video list from pose_model.cfg.data.video_dir
    #   for each video path:
    #     - does a corresponding detector corresponding bbox.csv exist?
    #     - if so, continue
    #       else
    #         - predict video using detector model (=> pred_df)
    #         - call:
    
    # generate_cropped_video(
    #     video_path=video_path,
    #     output_directory=detector_model.get_cropped_data_dir(),
    #     detector_cfg=detector_model.cfg,
    #     pred_df=pred_df)
    pass

def generate_cropped_csv_file(pose_model, detector_model):
    # Read csv file from pose_model.cfg.data.csv_file
    # TODO: reuse header_rows logic from datasets.py
    csv_file = Path(pose_model.cfg.data.csv_file)
    if not csv_file.is_absolute():
        csv_file = Path(pose_model.cfg.data.data_dir) / csv_file
    csv_data = pd.read_csv(csv_file, header=[0, 1, 2], index_col=0)
    
    # read bbox csv file from detector_model.get_cropped_data_dir() / "bbox.csv"
    bbox_file = detector_model.get_cropped_data_dir() / "bbox.csv"
    bbox_data = pd.read_csv(bbox_file, index_col=0)

    def transform_bbox_to_csv_df_format(bbox_df, csv_df):
        """
        Transforms the bbox DataFrame to have a column MultiIndex 
        compatible with the csv_data DataFrame.
        """
        # Get unique scorers and keypoints from csv_data
        scorers = csv_df.columns.get_level_values(0).unique()
        keypoints = csv_df.columns.get_level_values(1).unique()

        # Create a MultiIndex for the transformed bbox data
        multi_index = pd.MultiIndex.from_product([scorers, keypoints, ['x', 'y']])

        # Repeat bbox_data for each scorer and keypoint combination
        repeated_bbox = pd.concat([bbox_df[['x', 'y']]] * len(scorers) * len(keypoints), axis=1)
        repeated_bbox.columns = multi_index

        return repeated_bbox
    

    bbox_data = transform_bbox_to_csv_df_format(bbox_data, csv_data)
    csv_data = csv_data - bbox_data

    # Save out new df in pose_model.get_cropped_csv_file_path()
    pose_model.get_cropped_csv_file_path().parent.mkdir(parents=True, exist_ok=True)
    csv_data.to_csv(pose_model.get_cropped_csv_file_path())


def remap_preds_csv_for_labeled_frames(preds_df, detector_model, remapped_preds_file):
    # This will resemble the reverse of generate_cropped_csv_file.

    # read bbox csv file from detector_model.get_cropped_data_dir() / "bbox.csv"
    # for each row
    #   - look up the bbox
    #   - for each keypoint, add the bbox point
    # save out new df in pose_model.remapped_preds_file
    pass


@typechecked
def generate_cropped_video(
    video_path: Path,
    detector_model_dir: Path,
    detector_cfg: DictConfig,
    pred_df: Optional[pd.DataFrame] = None,
) -> None:
    video_path = Path(video_path)

    if pred_df is None:
        preds_file = detector_model_dir / "video_preds" / (video_path.stem + ".csv")
        pred_df = pd.read_csv(preds_file, header=[0, 1, 2], index_col=0)

    # Save cropping bboxes
    bbox_df = _compute_bbox_df(
        pred_df, list(detector_cfg.anchor_keypoints), crop_ratio=detector_cfg.crop_ratio
    )
    output_bbox_path = (
        detector_model_dir / "cropped_videos" / (video_path.stem + "_bbox.csv")
    )
    output_bbox_path.parent.mkdir(parents=True, exist_ok=True)
    bbox_df.to_csv(output_bbox_path)

    # Generate a cropped video for debugging purposes.
    _crop_video_moviepy(video_path, bbox_df, detector_model_dir / "cropped_videos")


class DetectorModel:
    def __init__(self, model_path: Path):
        self.model_path = model_path

    def get_cropped_data_dir(self):
        return self.model_path / "cropped_images"

    def get_cropped_video_dir(self):
        return self.model_path / "cropped_videos"
    

class PoseModel:
    def __init__(self, model_path: Path):
        self.model_path = model_path
        self.cfg = OmegaConf.load(model_path / "config.yaml")

    def get_cropped_predictions_csv_path(self):
        return self.model_path / "cropped_predictions.csv"

    def get_cropped_csv_file_path(self):
        return self.model_path / "cropped_labels" / Path(self.cfg.data.csv_file).name

    def get_cropped_cfg(self, detector_model):
        cropped_cfg = copy.deepcopy(self.cfg)
        cropped_cfg.data.data_dir = str(detector_model.get_cropped_data_dir())
        cropped_cfg.data.video_dir = str(detector_model.get_cropped_video_dir())
        cropped_cfg.eval.test_videos_directory = cropped_cfg.data.video_dir
        cropped_cfg.data.csv_file = str(self.get_cropped_csv_file_path())
        return cropped_cfg
