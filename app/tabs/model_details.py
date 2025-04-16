from functools import partial
import logging
from pathlib import Path
from typing import List, Optional

from nicegui import ui, background_tasks, run
from .. import config
from ..components.file_picker import FilePicker
from ..dao.model import Model
from ..dao.data import DataDao

# Set up logging
logger = logging.getLogger(__name__)


class ModelDetails:
    def __init__(self, model_name: str):
        self.model_name = model_name.replace(":", "/")
        self.model: Optional[Model] = None
        self.selected_files: List[str] = []
        self.model_loaded = False
        self.data_dao = DataDao(config.data_dir)
        self.videos_list_loaded = False
        self.videos_list = []

        # Create a file picker for prediction files
        self.file_picker = FilePicker(
            dirs_only=False,
            multiple=True,
            button_text="Choose files to predict on",
            button_icon="upload_file",
            label_prefix="Selected files: ",
            on_selection_change=self.on_files_selected,
        )

    def on_files_selected(self, files: List[str]) -> None:
        """Handle when files are selected for prediction"""
        self.selected_files = files
        logging.info(f"Selected {len(files)} files for prediction")
        # Here you would implement the prediction logic
        # For now, we'll just log the files


    async def load_model(self):
        """Load the model details."""
        # Find the model in the list
        models = await Model.async_list()
        for model in models:
            if model.name == self.model_name:
                self.model = model
                self.file_picker.initial_path = model._config.data.data_dir
                break

        self.model_loaded = True

        self.build.refresh()

    
    async def load_videos_list(self):
        """Load the videos list."""
        self.videos_list_loaded = True
        # Find the model in the list
        self.videos_list = await self.data_dao.videos_list()


        self.build_prediction_section.refresh()

    @ui.refreshable
    def build(self):
        ui.page_title(f"Lightning Pose | Model: {self.model_name}")

        # Load model details
        # ui.loading("Loading model details...")
        if not self.model_loaded:
            background_tasks.create(self.load_model())

        if not self.videos_list_loaded:
            background_tasks.create(self.load_videos_list())

        # Display model name as a header
        ui.label(self.model_name).classes("text-2xl font-bold")
        if not self.model_loaded:
            ui.label(f"Loading...").classes("text-gray-500")
            return

        # Display model type if available
        if self.model and self.model.model_type:
            ui.label(f"Type: {self.model.model_type}").classes("text-gray-500")
        else:
            ui.label("Model type not available").classes("text-gray-500")

        # Add a divider
        ui.separator()

        # Add Prediction section
        with ui.card().classes("w-full"):
            ui.label("Prediction").classes("text-xl font-bold")

            # Add file picker for selecting files to predict on
            self.file_picker.build()

            # Add a predict button that will be enabled when files are selected
            predict_button = ui.button(
                "Run Prediction",
                on_click=lambda: self.run_prediction(),
                icon="play_arrow",
            )
            predict_button.enabled = False

            # Update button state when files are selected
            def update_button_state():
                predict_button.enabled = len(self.selected_files) > 0

            # Override the on_files_selected method to also update button state
            original_on_files_selected = self.on_files_selected

            def on_files_selected_with_button_update(files):
                original_on_files_selected(files)
                update_button_state()
                self.build_prediction_section.refresh()

            self.file_picker.on_selection_change = on_files_selected_with_button_update

        self.build_prediction_section()


    async def run_prediction(self):
        """Run prediction on the selected files"""
        if not self.selected_files:
            ui.notify("Please select files to predict on", type="warning")
            return

        ui.notify(
            f"Running prediction on {len(self.selected_files)} files...", type="info"
        )

        from cli.commands import predict
        from lightning_pose.model import Model as CoreModel

        model = CoreModel.from_dir(Path(config.model_dir) / self.model.name)

        first_file = self.selected_files[0]

        await run.cpu_bound(
            predict._predict_multi_type, model, Path(first_file), True, True
        )

    @ui.refreshable
    def build_prediction_section(self):
        # Add Prediction section
        with ui.card().classes("w-full"):
            ui.label("Visualization").classes("text-xl font-bold")
            with ui.splitter().classes("w-full") as splitter:
                with splitter.before:
                    ui.label("Before")
                    @ui.refreshable
                    def visualizer_window(index=0):
                        if len(self.videos_list) > 0:
                            ui.video(src=self.videos_list[index])
                        else:
                            ui.label("No files selected")
                        class VW:
                            pass
                        def switch_media(index2):
                            print(f"Switching media to {index2}")
                            #v.set_source(self.selected_files[index2])
                            visualizer_window.refresh(index=index2)
                        handle = VW()
                        handle.switch_media = switch_media
                        return handle
                    vw = visualizer_window()
                    
                with splitter.after:
                    ui.label("After")
                    def visualizer_settings_panel():
                        with ui.list().classes("w-full"):
                            for i, file in enumerate(self.videos_list):
                            # for i, file in enumerate(self.selected_files):
                                ui.item(str(file), on_click=partial(vw.switch_media, index2=i))
                    visualizer_settings_panel()