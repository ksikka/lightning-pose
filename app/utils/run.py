import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, TypeVar, ParamSpec
import logging # Optional: for logging shutdown

P = ParamSpec('P')
R = TypeVar('R')

# Optional: configure a logger
log = logging.getLogger(__name__)

class ThreadPool:
    """
    Manages a dedicated ThreadPoolExecutor for running I/O-bound tasks.
    Each instance of Pool creates and owns its own executor.
    """
    def __init__(self, max_workers: int = 4):
        """
        Initializes the Pool with a specific number of workers and creates
        a dedicated ThreadPoolExecutor.

        Args:
            max_workers: Maximum number of worker threads for the pool's executor.
        """
        self.max_workers = max_workers
        # Create a dedicated executor for this Pool instance
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            # Optional: thread_name_prefix for easier debugging
            thread_name_prefix=f'IOPool-{id(self)}-' 
        )
        log.debug(f"Created {self.__class__.__name__} with {max_workers=}, executor={self.executor}")

    async def run_iobound(
        self, 
        callback: Callable[P, R], 
        *args: P.args, 
        **kwargs: P.kwargs
    ) -> R | None:
        """
        Run an I/O-bound function in the pool's dedicated thread executor.
        
        Args:
            callback: The function to run
            *args: Positional arguments to pass to the callback
            **kwargs: Keyword arguments to pass to the callback
            
        Returns:
            The result of the callback function, or None if the task was cancelled
            or the executor was shut down.
            
        Raises:
            RuntimeError: If the executor has been shut down before calling.
        """
        # Check if executor is still running (optional but good practice)
        # Accessing _shutdown directly is fragile, but ThreadPoolExecutor lacks a public is_running property
        if getattr(self.executor, '_shutdown', False):
             log.warning(f"Attempted to run task on already shutdown executor: {self.executor}")
             raise RuntimeError("Cannot schedule new futures after shutdown")
            
        try:
            loop = asyncio.get_running_loop()
            # Use the instance's dedicated executor
            return await loop.run_in_executor(self.executor, partial(callback, *args, **kwargs))
        except RuntimeError as e:
            # run_in_executor raises RuntimeError if loop is closing or executor is shut down
            # Log the specific error if it's unexpected
            if 'cannot schedule new futures after shutdown' not in str(e) and \
               'cannot schedule new futures after interpreter shutdown' not in str(e) and \
               'Event loop is closed' not in str(e):
                 log.exception("Unexpected RuntimeError in run_iobound")
                 raise # Re-raise unexpected errors
            else:
                 log.warning(f"Task scheduling failed on {self.executor}: {e}")
        except asyncio.CancelledError:
            log.debug(f"Task cancelled in {self.executor}")
            # Task was cancelled
            pass
        return None # Indicate failure or cancellation

    def shutdown(self, wait: bool = True, *, cancel_futures: bool = False):
        """
        Shuts down the ThreadPoolExecutor associated with this Pool instance.

        Args:
            wait: If True, waits for all pending futures to complete.
            cancel_futures: If True (and Python >= 3.9), cancels pending futures
                            that have not started. Requires wait=True.
        """
        log.debug(f"Shutting down executor {self.executor} (wait={wait}, cancel_futures={cancel_futures})")
        # Ensure compatibility with Python < 3.9 for cancel_futures
        import sys
        if sys.version_info >= (3, 9):
            self.executor.shutdown(wait=wait, cancel_futures=cancel_futures)
        else:
            if cancel_futures:
                log.warning("cancel_futures=True requires Python 3.9+. Ignoring.")
            self.executor.shutdown(wait=wait)
        log.debug(f"Executor {self.executor} shutdown complete.")

    # Implements __enter__ and __exit__ for use as a context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()