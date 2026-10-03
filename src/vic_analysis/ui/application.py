import click
from PySide6.QtWidgets import QApplication

from vic_analysis.read.data_loader import load_data
from vic_analysis.read.stylesheet import QT_STYLE, load_stylesheet
from vic_analysis.ui.controller.activity_bar_controller import ActivityBarController
from vic_analysis.ui.controller.file_system_controller import FileSystemController
from vic_analysis.ui.controller.histogram_controller import HistogramController
from vic_analysis.ui.controller.main_controller import MainController
from vic_analysis.ui.controller.spectral_controller import SpectralController
from vic_analysis.ui.model.app_config import AppConfig
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.model.plot_model import PlotModel
from vic_analysis.ui.view.activity_bar import ActivityBar
from vic_analysis.ui.view.file_system_view import FileSystemView
from vic_analysis.ui.view.hisotgram_view import HistogramView
from vic_analysis.ui.view.image_view import ImageView
from vic_analysis.ui.view.main_view import MainView
from vic_analysis.ui.view.main_window import MainWindow
from vic_analysis.ui.view.spectral_view import SpectralView


def create_application() -> QApplication:
    """Create and configure the Qt application instance."""
    application = QApplication()
    application.setApplicationName("VIC Analysis")
    application.setStyleSheet(load_stylesheet(QT_STYLE))
    return application


def apply_config_settings(state: AppState, config: AppConfig) -> None:
    if config.home_directory is not None:
        state.home_directory = config.home_directory
    if config.colormap is not None:
        state.color_map = config.colormap
    if config.starting_image is not None:
        image_data = load_data(config.starting_image)
        state.current_image = image_data


class Application:
    def __init__(self, config: str | None = None) -> None:
        self._qtapp = create_application()

        self.state = AppState()
        self.plot_model = PlotModel()

        self.image_view = ImageView(self.plot_model)
        self.histogram_view = HistogramView()
        self.spectral_view = SpectralView(self.plot_model)
        self.activity_bar = ActivityBar()
        self.file_system_view = FileSystemView()

        self.main_view = MainView(
            self.activity_bar,
            self.image_view,
            self.spectral_view,
            self.histogram_view,
            self.file_system_view,
        )

        self._main_controller = MainController(
            self.main_view, self.state, self.plot_model
        )
        self._histogram_controller = HistogramController(
            self.histogram_view, self.state
        )
        self._activity_bar_controller = ActivityBarController(
            self.activity_bar, self.state
        )
        self._file_system_controller = FileSystemController(
            self.file_system_view, self.state
        )
        self._spectral_controller = SpectralController(
            self.plot_model, self.spectral_view, self.state
        )

        self.window = MainWindow(self.main_view, self._main_controller)

        if config is not None:
            cfg = AppConfig.from_json(config)
            apply_config_settings(self.state, cfg)

    def run(self) -> int:
        self.window.show()
        return self._qtapp.exec()


@click.command()
@click.option("--config", type=str, default=None)
def run(config: str | None = None) -> int:
    """Start the desktop application and return Qt's exit code."""
    app = Application(config)
    return app.run()
