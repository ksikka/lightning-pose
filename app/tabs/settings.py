from nicegui import ui

from ..components.file_picker import FilePicker
from .. import config


class Settings:

    def build(self):
        ui.page_title("Lightning Pose | Settings")
        ui.label("Settings").classes("text-2xl font-bold")
        ui.separator()
        with ui.row():
            ui.label("Model directory")

            def set_model_dir(paths):
                config.model_dir = paths[0]
            FilePicker(
                dirs_only=True, on_selection_change=set_model_dir
            ).build()

        with ui.row():
            ui.label("Video directory (video_dir): ")
            def set_video_dir(paths):
                config.video_dir = paths[0]
            FilePicker(
                dirs_only=True, on_selection_change=set_video_dir
            ).build()

