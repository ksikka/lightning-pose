from pathlib import Path
from typing import List
from dataclasses import dataclass


@dataclass
class LabeledFrameDataset:
    data_dir: Path
    csv_file: Path
    keypoint_names: List[str]

    def get_labels_file_path(self):
        pass


@dataclass
class VideoDataset:
    video_dir: Path


TRAINING_DATASET = 1