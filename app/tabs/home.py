from nicegui import ui

from ..components.file_picker import FilePicker


class Home:

    def __init__(self):
        self.chosen_path = None
        self.file_picker = FilePicker(
            dirs_only=True, on_selection_change=self.on_path_selected
        )

    def on_path_selected(self, paths):
        if paths:
            self.chosen_path = paths[0]
            # You can add additional logic here if needed

    def build(self):
        ui.page_title("Lightning Pose | Home")
        ui.label("Welcome to Lightning Pose")
        ui.label("Select a directory to get started:")
        self.file_picker.build()
