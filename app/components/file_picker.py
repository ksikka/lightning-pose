from typing import Callable, List, Optional, Union

from nicegui import ui

from .local_file_picker_dialog import local_file_picker_dialog


class FilePicker:
    """
    A reusable component that provides a button to open a file picker dialog
    and displays the selected files.
    """

    def __init__(
        self,
        initial_path: str = "~",
        upper_limit: Optional[str] = None,
        dirs_only: bool = False,
        multiple: bool = False,
        on_selection_change: Optional[Callable[[List[str]], None]] = None,
        button_text: str = "Choose file",
        button_icon: str = "folder",
        label_prefix: str = "Selected: ",
    ):
        """
        Initialize the FilePicker component.

        Args:
            initial_path: The initial path to open the file picker dialog at
            upper_limit: The upper limit path for the file picker dialog
            dirs_only: Whether to only allow selecting directories
            multiple: Whether to allow selecting multiple files
            on_selection_change: Callback function to call when selection changes
            button_text: Text to display on the button
            button_icon: Icon to display on the button
            label_prefix: Prefix for the label that displays selected files
        """
        self.initial_path = initial_path
        self.upper_limit = upper_limit
        self.dirs_only = dirs_only
        self.multiple = multiple
        self.on_selection_change = on_selection_change
        self.button_text = button_text
        self.button_icon = button_icon
        self.label_prefix = label_prefix
        self.selected_paths: List[str] = []

    async def pick_files(self) -> None:
        """Open the file picker dialog and update the selected paths."""
        result = await local_file_picker_dialog(
            self.initial_path,
            upper_limit=self.upper_limit,
            dirs_only=self.dirs_only,
            multiple=self.multiple,
        )

        if result:
            self.selected_paths = result
            self.selected_paths_label.refresh()

            if self.on_selection_change:
                self.on_selection_change(self.selected_paths)

    @ui.refreshable
    def selected_paths_label(self):
        """Display the selected paths."""
        if not self.selected_paths:
            ui.label("")
        elif len(self.selected_paths) == 1:
            ui.label(f"{self.label_prefix}{self.selected_paths[0]}")
        else:
            ui.label(f"{self.label_prefix}{len(self.selected_paths)} items selected")
            with ui.expansion("Show selected items"):
                for path in self.selected_paths:
                    ui.label(path)

    def build(self) -> None:
        """Build the FilePicker component."""
        with ui.row():
            ui.button(self.button_text, on_click=self.pick_files, icon=self.button_icon)
            self.selected_paths_label()
