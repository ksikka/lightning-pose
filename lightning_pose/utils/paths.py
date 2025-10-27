import re
from pathlib import Path, PurePath, PurePosixPath, PureWindowsPath

from lightning_pose.data.datatypes import Project
from lightning_pose.data.keys import (
    VideoFileKey,
    VideoFrameKey,
    SessionKey,
    LabelFileKey,
    ViewName,
)  # Add LabelFileKey import


class PathParseException(Exception):
    pass


def _check_relative_and_normalize(path: Path | str) -> PurePath:
    path = PureWindowsPath(path) if "\\" in str(path) else PurePosixPath(path)
    if path.is_absolute():
        raise ValueError("Argument must be relative path: " + str(path))

    return PurePosixPath(str(path).replace("\\", "/"))


class ProjectPathUtil:
    def __init__(self, project: Project):
        self._conf: Project = project

    def _is_multiview(self) -> bool:
        return bool(self._conf.views and len(self._conf.views) > 1)

    def get_video_file_path(self, video_file_key: VideoFileKey) -> Path:
        """Constructs a Path object for a video file given a VideoFileKey."""
        if self._is_multiview():
            return (
                Path("videos")
                / f"{video_file_key.session_key}_{video_file_key.view}.mp4"
            )
        else:
            return Path("videos") / f"{video_file_key.session_key}.mp4"

    def extract_video_file_key(self, path: Path | str) -> VideoFileKey:
        """Parses a video file path and extracts a VideoFileKey."""
        path = _check_relative_and_normalize(path)
        if self._is_multiview():
            pattern = r"videos/(?P<session>[^/]+)_(?P<view>[^/_]+)\.mp4"
        else:
            pattern = r"videos/(?P<session>[^/]+)\.mp4"

        m = re.match(pattern, path.as_posix())
        if not m:
            raise PathParseException(
                f"Could not parse video file path: {path.as_posix()}, multiview={self._is_multiview()}"
            )

        if self._is_multiview():
            return VideoFileKey(
                session_key=m.group("session"),
                view=m.group("view"),
            )
        else:
            return VideoFileKey(
                session_key=m.group("session"),
                view=None,
            )

    def get_label_frame_path(self, key: VideoFrameKey) -> Path:
        """Constructs a Path object for a label image file given a VideoFrameKey."""
        if self._is_multiview():
            # Example: labeled-data/sessionkey_view/frame_123.png
            return (
                Path("labeled-data")
                / f"{key.session_key}_{key.view}"
                / f"frame_{key.frame_index}.png"
            )
        else:
            # Example: labeled-data/sessionkey/frame_123.png
            return (
                Path("labeled-data")
                / f"{key.session_key}"
                / f"frame_{key.frame_index}.png"
            )

    def extract_label_frame_key(self, path: Path | str) -> VideoFrameKey:
        """Parses a label image file path and extracts a VideoFrameKey."""
        path = _check_relative_and_normalize(path)
        if self._is_multiview():
            # Example: labeled-data/sessionkey_view/frame_123.png
            pattern = r"labeled-data/(?P<session>[^/]+)_(?P<view>[^/_]+)/frame_(?P<frameindex>\d+)\.png"
        else:
            # Example: labeled-data/sessionkey/frame_123.png
            pattern = r"labeled-data/(?P<session>[^/]+)/frame_(?P<frameindex>\d+)\.png"

        m = re.match(pattern, path.as_posix())
        if not m:
            raise PathParseException(
                f"Could not parse label frame path: {path.as_posix()}, multiview={self._is_multiview()}"
            )

        session_key = m.group("session")
        frame_index = int(m.group("frameindex"))  # Convert frame index to integer

        if self._is_multiview():
            view = m.group("view")
            return VideoFrameKey(
                session_key=session_key, frame_index=frame_index, view=view
            )
        else:
            return VideoFrameKey(
                session_key=session_key, frame_index=frame_index, view=None
            )

    def get_label_file_path(self, key: LabelFileKey, view: ViewName) -> Path:
        """Constructs a Path for a label data CSV file given a LabelFileKey."""
        if self._is_multiview():
            return Path("labeled-data/label-files") / f"{key}_{view}.csv"
        else:
            return Path("labeled-data/label-files") / f"{key}.csv"

    def extract_label_file_keys(
        self, path: Path | str
    ) -> tuple[LabelFileKey, ViewName | None]:
        """Parses a label data CSV file path and extracts a LabelFileKey."""
        path = _check_relative_and_normalize(path)
        if self._is_multiview():
            pattern = r"labeled-data/label-files/(?P<labelfilekey>[^/]+)_(?P<view>[^/_]+)\.csv"
        else:
            pattern = r"labeled-data/label-files/(?P<labelfilekey>[^/]+)\.csv"

        m = re.match(pattern, path.as_posix())
        if not m:
            raise PathParseException(
                f"Could not parse label file path: {path.as_posix()}, multiview={self._is_multiview()}"
            )

        if self._is_multiview():
            return (m.group("labelfilekey"), m.group("view"))
        else:
            return (m.group("labelfilekey"), None)

    def get_center_frames_path(self, key: VideoFileKey) -> Path:
        """labeled-data/<sessionkey>_<view>/center_frames.txt"""
        if self._is_multiview():
            return (
                Path("labeled-data")
                / f"{key.session_key}_{key.view}"
                / "center_frames.txt"
            )
        else:
            return Path("labeled-data") / f"{key.session_key}" / "center_frames.txt"

    def extract_center_frames_key(self, path: Path | str) -> VideoFileKey:
        """extract key from labeled-data/<sessionkey>_<view>/center_frames.txt"""
        path = _check_relative_and_normalize(path)
        if self._is_multiview():
            pattern = (
                r"labeled-data/(?P<session>[^/]+)_(?P<view>[^/_]+)/center_frames\.txt"
            )
        else:
            pattern = r"labeled-data/(?P<session>[^/]+)/center_frames\.txt"

        m = re.match(pattern, path.as_posix())
        if not m:
            raise PathParseException(
                f"Could not parse center frames path: {path.as_posix()}, multiview={self._is_multiview()}"
            )

        if self._is_multiview():
            return VideoFileKey(session_key=m.group("session"), view=m.group("view"))
        else:
            return VideoFileKey(session_key=m.group("session"), view=None)

    def get_session_calibration_path(self, session_key: SessionKey) -> Path:
        """calibrations/<sessionkey>.csv"""
        return Path("calibrations") / f"{session_key}.csv"

    def extract_session_key_from_calibration_path(self, path: Path | str) -> SessionKey:
        """extracts session key from calibrations/<sessionkey>.csv"""
        path = _check_relative_and_normalize(path)
        pattern = r"calibrations/(?P<session>[^/]+)\.csv"
        m = re.match(pattern, path.as_posix())
        if not m:
            raise PathParseException(
                f"Could not parse session calibration path: {path.as_posix()}"
            )
        return m.group("session")

    def get_project_calibration_path(self) -> Path:
        """calibration.csv"""
        return Path("calibration.csv")

    def get_calibration_backup_path(
        self, session_key: SessionKey, time_ns: int
    ) -> Path:
        """calibration_backups/<sessionkey>.<time_ns>.csv"""
        return Path("calibration_backups") / f"{session_key}.{time_ns}.csv"

    def extract_calibration_backup_info(
        self, path: Path | str
    ) -> tuple[SessionKey, int]:
        """extracts session key and time from calibration_backups/<sessionkey>.<time_ns>.csv"""
        path = _check_relative_and_normalize(path)
        pattern = r"calibration_backups/(?P<session>[^/]+)\.(?P<time>\d+)\.csv"
        m = re.match(pattern, path.as_posix())
        if not m:
            raise PathParseException(
                f"Could not parse calibration backup path: {path.as_posix()}"
            )
        return m.group("session"), int(m.group("time"))
