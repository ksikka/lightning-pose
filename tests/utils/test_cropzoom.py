import copy
import filecmp
import shutil
from pathlib import Path

import pandas as pd
from omegaconf import OmegaConf

from lightning_pose.utils.cropzoom import (
    generate_cropped_labeled_frames,
    generate_cropped_video,
)


# TODO: Move to utils.
def compare_directories(dir1: Path, dir2: Path) -> int | dict:
    """
    Compares files in two directories recursively.

    Args:
      dir1: Path to the first directory.
      dir2: Path to the second directory.

    Returns:
      Number of matched files if the directories are identical, or
      a dictionary with the following keys if the directories are different:
        'mismatch': List of files that differ between the directories.
        'errors': List of files that couldn't be compared (e.g., due to permissions).
        'left_only': List of files that exist only in the first directory.
        'right_only': List of files that exist only in the second directory.
    """
    num_matches = 0
    empty_results = {
        "mismatch": [],
        "errors": [],
        "left_only": [],
        "right_only": [],
    }
    results = copy.deepcopy(empty_results)

    dircmp_result = filecmp.dircmp(dir1, dir2)

    # Compare common files
    for common_file in dircmp_result.common_files:
        if filecmp.cmp(dir1 / common_file, dir2 / common_file, shallow=False):
            num_matches += 1
        else:
            results["mismatch"].append(common_file)

    # Recursively compare subdirectories
    for sub_dir in dircmp_result.common_dirs:
        sub_results = compare_directories(dir1 / sub_dir, dir2 / sub_dir)
        if isinstance(sub_results, int):
            num_matches += sub_results
        else:
            results["mismatch"].extend(sub_results["mismatch"])
            results["errors"].extend(sub_results["errors"])
            results["left_only"].extend(sub_results["left_only"])
            results["right_only"].extend(sub_results["right_only"])

    # Add files unique to each directory and any errors
    results["errors"].extend(dircmp_result.common_funny)
    results["left_only"].extend(dircmp_result.left_only)
    results["right_only"].extend(dircmp_result.right_only)

    if results == empty_results:
        return num_matches
    return results


def test_generate_cropped_labeled_frames(tmp_path, request):
    # Setup output directory.
    output_directory = tmp_path / "test_model"
    shutil.copytree(
        request.path.parent / "test_cropzoom_data" / "test_model_output",
        output_directory,
        dirs_exist_ok=True,
    )

    root_directory = request.path.parent / "test_cropzoom_data" / "test_data"
    detector_cfg = OmegaConf.create(
        {"crop_ratio": 1.5, "anchor_keypoints": ["A_head", "D_tailtip"]}
    )
    generate_cropped_labeled_frames(
        root_directory, output_directory, detector_cfg=detector_cfg
    )

    comparison = compare_directories(
        output_directory / "cropped_images",
        request.path.parent
        / "test_cropzoom_data"
        / "expected_model_output"
        / "cropped_images",
    )
    assert comparison == 23


def test_generate_cropped_video(tmp_path, request):
    # Setup output directory.
    output_directory = tmp_path / "test_model"
    shutil.copytree(
        request.path.parent / "test_cropzoom_data" / "test_model_output",
        output_directory,
        dirs_exist_ok=True,
    )

    video_directory = (
        request.path.parent / "test_cropzoom_data" / "test_data" / "videos"
    )
    detector_cfg = OmegaConf.create(
        {"crop_ratio": 1.5, "anchor_keypoints": ["A_head", "D_tailtip"]}
    )

    for video_path in video_directory.iterdir():
        generate_cropped_video(video_path, output_directory, detector_cfg=detector_cfg)

    comparison = compare_directories(
        output_directory / "cropped_videos",
        request.path.parent
        / "test_cropzoom_data"
        / "expected_model_output"
        / "cropped_videos",
    )
    assert comparison == 4
