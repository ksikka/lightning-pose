from pathlib import Path
from typing import List
from nicegui import run
import asyncio
from app.utils.ffprobe import ffprobe
from app.utils.run import ThreadPool
import logging


class DataDao:
    def __init__(self, data_dir: str | Path):
        """
        Args:
            data_dir: Path to the data directory
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.is_dir():
            # Added a check for directory existence
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")

    def _get_all_mp4_files_sync(self) -> List[Path]:
        """
        Synchronously finds all .mp4 files recursively in the data directory.

        Returns:
            List of Path objects representing video files with .mp4 extension, sorted.
        """
        video_files = list(self.data_dir.rglob("*.mp4"))
        # Sort for consistent ordering
        return sorted(video_files)

    async def videos_list(self) -> List[Path]:
        """
        Asynchronously returns a list of all video file paths with the .mp4 extension
        found recursively within the data directory.

        Returns:
            List of Path objects representing video files.
        """
        logging.info(f"Scanning for .mp4 files in {self.data_dir}...")
        # Use run.io_bound to run the synchronous file scanning in a separate thread
        video_files = await run.io_bound(self._get_all_mp4_files_sync)
        logging.info(f"Found {len(video_files)} .mp4 files.")
        return video_files

    async def validate_videos_codec(self, videos_to_check: List[Path], expected_codec: str = "h264", max_workers: int = 4) -> List[Path]:
        """
        Validates a list of video files to check if they use the expected video codec.

        Uses a ThreadPool to run ffprobe checks concurrently.

        Args:
            videos_to_check: A list of Path objects representing video files to validate.
            expected_codec: The video codec name to check for (e.g., "h264"). Defaults to "h264".
            max_workers: Maximum number of threads to use for checking codecs.

        Returns:
            A list of Path objects representing video files that DO NOT use the expected codec
            or where the codec check failed.
        """
        logging.info(f"Validating codec '{expected_codec}' for {len(videos_to_check)} videos using up to {max_workers} workers...")
        if not videos_to_check:
            logging.info("No videos provided for validation.")
            return []

        # --- Helper function to check codec for a single video ---
        def _check_codec_sync(video_path: Path) -> Optional[bool]:
            """ Checks if a video uses the expected codec. Runs synchronously. """
            try:
                # Ensure ffprobe receives a string path
                info = ffprobe(str(video_path))
                # Check if ffprobe returned valid info and contains video stream details
                if info and 'streams' in info:
                    for stream in info['streams']:
                         # Check only video streams for the codec name
                        if stream.get('codec_type') == 'video':
                            actual_codec = stream.get("codec_name", "").lower()
                            logging.debug(f"Video: {video_path.name}, Codec found: {actual_codec}")
                            return actual_codec == expected_codec.lower()
                # If no video stream found or codec_name missing
                logging.warning(f"Could not determine video codec for: {video_path}")
                return None # Indicate uncertainty or lack of video stream
            except Exception as e:
                # Log the error for debugging
                logging.error(f"Error checking video {video_path}: {e}", exc_info=False) # Set exc_info=True for full traceback
                return False # Treat errors as validation failure (not expected codec)
        # --- End of helper function ---

        invalid_videos: List[Path] = []
        results = []

        # Use ThreadPool for concurrent I/O bound tasks (ffprobe)
        try:
            with ThreadPool(max_workers=max_workers) as pool:
                tasks = [
                    pool.run_iobound(_check_codec_sync, video_path)
                    for video_path in videos_to_check
                ]
                # Wait for all tasks to complete
                # gather will preserve the order corresponding to videos_to_check
                results = await asyncio.gather(*tasks, return_exceptions=True) # Catch potential exceptions during gather

        except Exception as e:
             logging.error(f"An error occurred during thread pool execution: {e}", exc_info=True)
             # Depending on requirements, you might want to return all videos as invalid
             # or re-raise the exception. Here, we'll just log and proceed with any results gathered.
             pass # Continue to process any results obtained before the error

        # Process results to find videos that are *not* using the expected codec
        for video_path, result in zip(videos_to_check, results):
            if isinstance(result, Exception):
                logging.error(f"Task for {video_path} failed with exception: {result}")
                invalid_videos.append(video_path) # Treat exceptions in tasks as invalid
            elif result is False or result is None:
                # result is False -> Codec is not the expected one OR ffprobe failed
                # result is None -> Codec could not be determined (no video stream, etc.)
                # In both cases, we list them as not meeting the criteria.
                invalid_videos.append(video_path)
            # elif result is True: # Video uses the expected codec, do nothing

        logging.info(f"Validation complete. Found {len(invalid_videos)} videos not using '{expected_codec}' codec (or failed check).")
        return invalid_videos
        