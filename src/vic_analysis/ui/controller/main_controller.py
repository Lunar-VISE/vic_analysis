from vic_analysis.read.data_loader import load_data
from vic_analysis.ui.controller.image_controller import ImageController
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.model.button_name import ButtonName
from vic_analysis.ui.model.plot_model import PlotModel
from vic_analysis.ui.view.image_view import ImageView
from vic_analysis.ui.view.main_view import MainView
from vic_analysis.ui.view.widgets.activity_button import ActivityButton


class MainController:
    def __init__(self, view: MainView, state: AppState, plot_model: PlotModel) -> None:
        self.state = state
        self.view = view
        self._plot_model = plot_model
        self.image_controllers: list[ImageController] = []

        self._register_image_view(self.view.image_view)

        self.state.activity_open_requested.connect(self.open_dock)
        self.state.activity_close_requested.connect(self.close_dock)
        self.state.save_requested.connect(self.choose_save_directory)

        self.view.histogram_dock.viewToggled.connect(
            view.activity_bar.histogram.setChecked
        )
        self.view.file_system_dock.viewToggled.connect(
            view.activity_bar.folder.setChecked
        )

    def add_image_view(self) -> None:
        image_view = ImageView(self._plot_model)
        self.view.add_image_view(image_view)
        self._register_image_view(image_view)

    def _register_image_view(self, image_view: ImageView) -> None:
        self.image_controllers.append(
            ImageController(self._plot_model, image_view, self.state)
        )

    def change_image(self) -> None:
        new_image_filepath = self.view.choose_image_file(self.state.home_directory)
        image_data = load_data(new_image_filepath)
        self.state.current_image = image_data

    def change_home_directory(self) -> None:
        new_home_directory = self.view.choose_home_directory(self.state.home_directory)
        self.state.home_directory = new_home_directory

    def choose_save_directory(self) -> None:
        save_directory = self.view.choose_save_directory(self.state.home_directory)
        self.state.save_directory_selected.emit(save_directory)

    def open_dock(self, button: ActivityButton) -> None:
        match button.name:
            case ButtonName.HISTOGRAM:
                dock = self.view.histogram_dock
            case ButtonName.FOLDER:
                dock = self.view.file_system_dock
        dock.toggleView(True)

    def close_dock(self, button: ActivityButton) -> None:
        match button.name:
            case ButtonName.HISTOGRAM:
                dock = self.view.histogram_dock
            case ButtonName.FOLDER:
                dock = self.view.file_system_dock
        dock.toggleView(False)
