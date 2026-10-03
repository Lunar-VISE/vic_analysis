from pathlib import Path

from vic_analysis.read.data_loader import load_data
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.view.file_system_view import FileSystemView


class FileSystemController:
    def __init__(self, view: FileSystemView, state: AppState) -> None:
        self.view = view
        self.state = state

        self.state.home_directory_changed.connect(self._set_root_dir)
        self.view.file_selected.connect(self._on_file_select)

    def _set_root_dir(self, root: Path) -> None:
        self.view.set_root_dir(root)

    def _on_file_select(self, file_path: Path) -> None:
        self.state.current_image = load_data(file_path)
