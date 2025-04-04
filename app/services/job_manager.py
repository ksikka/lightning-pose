import asyncio
import logging
import subprocess
import time
from typing import Dict, List, Optional, Callable
from nicegui import background_tasks

# Set up logging
logger = logging.getLogger(__name__)

class Job:
    def __init__(self, name: str, command: str, process: Optional[subprocess.Popen] = None):
        self.name = name
        self.command = command
        self.process = process
        self.start_time = time.time() if process else None
        self.status = "Running" if process else "Stopped"
        self.pid = process.pid if process else None

    def stop(self):
        if self.process:
            self.process.terminate()
            self.status = "Stopped"
            self.process = None
            self.pid = None

    def is_running(self) -> bool:
        if not self.process:
            return False
        return self.process.poll() is None

class JobManager:
    """
    Global job manager service that handles starting, stopping, and monitoring jobs.
    This is a singleton that persists across the application lifecycle.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.jobs: Dict[str, Job] = {}
        self.refresh_interval = 2  # seconds
        self.refresh_task = None
        self.status_change_callbacks: List[Callable] = []
        self._initialized = True
        
        # Start the background task to monitor jobs
        self._start_refresh_task()
    
    def _start_refresh_task(self):
        """Start the background task to monitor jobs if it's not already running."""
        if self.refresh_task is None:
            self.refresh_task = background_tasks.create(self._refresh_jobs_status())
    
    async def _refresh_jobs_status(self) -> None:
        """Periodically refresh the status of all jobs."""
        while True:
            logger.debug("Refreshing jobs status")
            status_changed = False
            
            for job in self.jobs.values():
                if job.process and not job.is_running():
                    job.status = "Stopped"
                    job.process = None
                    job.pid = None
                    status_changed = True
            
            if status_changed:
                self._notify_status_change()
                
            await asyncio.sleep(self.refresh_interval)
    
    def _notify_status_change(self):
        """Notify all registered callbacks that job status has changed."""
        for callback in self.status_change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")
    
    def register_status_change_callback(self, callback: Callable):
        """Register a callback to be called when job status changes."""
        if callback not in self.status_change_callbacks:
            self.status_change_callbacks.append(callback)
    
    def unregister_status_change_callback(self, callback: Callable):
        """Unregister a callback."""
        if callback in self.status_change_callbacks:
            self.status_change_callbacks.remove(callback)
    
    def start_job(self, name: str, command: str) -> bool:
        """
        Start a new job with the given name and command.
        Returns True if the job was started successfully, False otherwise.
        """
        if name in self.jobs and self.jobs[name].is_running():
            logger.warning(f"Job '{name}' is already running")
            return False

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                text=True
            )
            self.jobs[name] = Job(name, command, process)
            logger.info(f"Started job '{name}'")
            self._notify_status_change()
            return True
        except Exception as e:
            logger.error(f"Failed to start job '{name}': {e}")
            return False

    def stop_job(self, name: str) -> bool:
        """
        Stop a running job by name.
        Returns True if the job was stopped successfully, False otherwise.
        """
        if name in self.jobs:
            self.jobs[name].stop()
            logger.info(f"Stopped job '{name}'")
            self._notify_status_change()
            return True
        else:
            logger.warning(f"Job '{name}' not found")
            return False
    
    def get_jobs(self) -> Dict[str, Job]:
        """Get all jobs."""
        return self.jobs
    
    def get_job(self, name: str) -> Optional[Job]:
        """Get a job by name."""
        return self.jobs.get(name)
    
    def is_job_running(self, name: str) -> bool:
        """Check if a job is running."""
        job = self.jobs.get(name)
        return job is not None and job.is_running() 