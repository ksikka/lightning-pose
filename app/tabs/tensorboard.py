import logging
from nicegui import ui

from ..services.job_manager import JobManager
from ..components.iframe import Iframe

# Set up logging
logger = logging.getLogger(__name__)

class TensorBoard:
    def __init__(self) -> None:
        self.job_manager = JobManager()
        self.tensorboard_port = 6007
        self.tensorboard_url = f"http://localhost:{self.tensorboard_port}"
        
        # Register a callback to refresh the UI when job status changes
        self.job_manager.register_status_change_callback(self.build.refresh)

    def _build_status_card(self):
        """Build a card showing TensorBoard status and controls."""
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("TensorBoard Status").classes("text-h6")
                
                # Check if TensorBoard is running
                is_running = self.job_manager.is_job_running("tensorboard")
                
                if is_running:
                    ui.chip("Running", color="positive", text_color="white")
                    ui.button("Stop TensorBoard", on_click=lambda: self.stop_tensorboard(), icon="stop", color="negative")
                else:
                    ui.chip("Stopped", color="grey", text_color="white")
                    ui.button("Start TensorBoard", on_click=lambda: self.start_tensorboard(), icon="play_arrow", color="positive")
    
    def _build_iframe(self):
        """Build an iframe to display TensorBoard."""
        with ui.card().classes("w-full mt-4"):
            with ui.row().classes("w-full justify-between items-center"):
                ui.label("TensorBoard UI").classes("text-h6")
                
                # Add a refresh button
                ui.button("Refresh", on_click=lambda: self.refresh_iframe(), icon="refresh")
            
            # Create a container for the iframe
            self.iframe_container = ui.element("div").classes("w-full h-[600px]")
            
            with self.iframe_container:
                # Add the iframe using our custom component
                self.iframe = Iframe(self.tensorboard_url).classes("w-full h-full")
                
                # Show a message if TensorBoard is not running
                if not self.job_manager.is_job_running("tensorboard"):
                    with self.iframe_container:
                        ui.label("TensorBoard is not running. Start it to view visualizations.").classes("text-center p-4")
                        self.iframe.set_visibility(False)
    
    def start_tensorboard(self):
        """Start TensorBoard as a managed job."""
        if self.job_manager.start_job("tensorboard", f"tensorboard --logdir /home/ksikka/synced/outputs --port {self.tensorboard_port}"):
            ui.notify("TensorBoard started", type="positive")
            self.build.refresh()
        else:
            ui.notify("Failed to start TensorBoard", type="negative")
    
    def stop_tensorboard(self):
        """Stop the TensorBoard job."""
        if self.job_manager.stop_job("tensorboard"):
            ui.notify("TensorBoard stopped", type="info")
            self.build.refresh()
        else:
            ui.notify("Failed to stop TensorBoard", type="warning")
    
    def refresh_iframe(self):
        """Refresh the iframe content."""
        if self.job_manager.is_job_running("tensorboard"):
            self.iframe.set_visibility(True)
            self.iframe.set_source(self.tensorboard_url)
        else:
            self.iframe.set_visibility(False)
            with self.iframe_container:
                ui.label("TensorBoard is not running. Start it to view visualizations.").classes("text-center p-4")

    @ui.refreshable
    def build(self):
        """Build the TensorBoard tab UI."""
        ui.page_title("Lightning Pose | TensorBoard")
        
        # Build the status card
        self._build_status_card()
        
        # Build the iframe
        self._build_iframe() 