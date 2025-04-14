from pathlib import Path
from typing import List
from nicegui import run
import asyncio
from app.utils.ffprobe import ffprobe
from app.utils.run import ThreadPool


class DataDao:
    def __init__(self, data_dir: str | Path):
        """
        Args:
            data_dir: Path to the data directory
        """
        self.data_dir = Path(data_dir)
    
    def videos_list_unfiltered_sync(self) -> List[Path]:
        """
        Returns a list of video file paths.
            
        Returns:
            List of Path objects representing video files with .mp4 extension
        """
        video_files = []
        
        for file_path in self.data_dir.rglob("*.mp4"):
            video_files.append(file_path)

        # Sort for consistent ordering 
        return list(sorted(video_files))

    
    async def videos_list(self) -> List[Path]:
        """
        Returns a list of video file paths filtered to only include HEVC encoded videos.
        Uses the DataDao's Pool instance to process videos asynchronously.
            
        Returns:
            List of Path objects representing HEVC encoded video files with .mp4 extension
        """
        video_files = await run.io_bound(self.videos_list_unfiltered_sync)
        
        # Create a function to check if a video is HEVC encoded
        # This function is I/O bound (runs ffprobe)
        def is_hevc_encoded(video_path: Path) -> bool:
            try:
                # Ensure ffprobe receives a string path
                info = ffprobe(str(video_path)) 
                # Check if info is valid and contains codec_name
                return info and info.get("codec_name", "").lower() in ["h264"]
            except Exception as e:
                # Log the error for debugging
                print(f"Error checking video {video_path}: {e}") 
                return False
        
        with ThreadPool(max_workers=4) as pool:
            # Process videos asynchronously using the instance's pool
            tasks = [
                pool.run_iobound(is_hevc_encoded, video_path) 
                for video_path in video_files
            ]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks)
        
        # Filter videos based on results (handle potential None results from run_iobound)
        hevc_videos = [
            video_path 
            for video_path, is_hevc in zip(video_files, results) 
            if is_hevc is True # Explicitly check for True
        ]

        print("done")
        print(len(hevc_videos))
        
        return hevc_videos
        