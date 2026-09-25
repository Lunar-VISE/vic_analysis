from vic_analysis.read.data_loader import load_data
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.view.main_view import MainView


class MainController:
    def __init__(self, view: MainView, state: AppState) -> None:
        self.state = state
        self.view = view

        self.view.open_requested.connect(self.open_data)
        self.view.home_directory_change_requested.connect(self.change_home_directory)

        self.state.home_directory_changed.connect(self.view.update_home_directory)

    def open_data(self) -> None:
        filepath = self.view.choose_image_file()
        image_data = load_data(filepath)
        self.state.current_image = image_data

    def change_home_directory(self) -> None:
        filepath = self.view.choose_home_directory()
        self.state.home_directory_changed.emit(filepath)
