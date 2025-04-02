from nicegui import ui

from ..components.local_file_picker import local_file_picker


class Home:

    def __init__(self):
        self.chosen_path = None

    async def pick_file(self) -> None:
        result = await local_file_picker("~", upper_limit=None, dirs_only=True)
        assert len(result) == 1
        self.chosen_path = result[0]
        self.chosen_path_ui_label.refresh()

    @ui.refreshable
    def chosen_path_ui_label(self):
        text = f"Selected: {self.chosen_path}" if self.chosen_path is not None else ""
        ui.label(text)

    def build(self):
        ui.page_title("Lightning Pose | Home")
        self.chosen_path_ui_label()
        ui.button("Choose file", on_click=self.pick_file, icon="folder")
