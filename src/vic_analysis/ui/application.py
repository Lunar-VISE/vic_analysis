import click
from PySide6.QtWidgets import QApplication

from vic_analysis.read.data_loader import load_data
from vic_analysis.ui.controller.histogram_controller import HistogramController
from vic_analysis.ui.controller.image_controller import ImageController
from vic_analysis.ui.controller.main_controller import MainController
from vic_analysis.ui.model.app_config import AppConfig
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.styles import application_stylesheet
from vic_analysis.ui.view.hisotgram_view import HistogramView
from vic_analysis.ui.view.image_view import ImageView
from vic_analysis.ui.view.main_view import MainView
from vic_analysis.ui.view.main_window import MainWindow


def create_application() -> QApplication:
    """Create and configure the Qt application instance."""
    application = QApplication()
    application.setApplicationName("VIC Analysis")
    application.setStyleSheet(application_stylesheet())
    return application


def apply_config_settings(state: AppState, config: AppConfig) -> None:
    if config.home_directory is not None:
        state.home_directory_changed.emit(config.home_directory)
    if config.colormap is not None:
        state.color_map = config.colormap
    if config.starting_image is not None:
        image_data = load_data(config.starting_image)
        state.current_image = image_data


@click.command()
@click.option("--config", type=str, default=None)
def run(config: str | None = None) -> int:
    """Start the desktop application and return Qt's exit code."""

    application = create_application()

    state = AppState()

    image_view = ImageView()
    histogram_view = HistogramView()
    main_view = MainView(image_view, histogram_view)

    _main_controller = MainController(main_view, state)
    _image_controller = ImageController(image_view, state)
    _histogram_controller = HistogramController(histogram_view, state)

    window = MainWindow(main_view)

    if config is not None:
        cfg = AppConfig.from_json(config)
        apply_config_settings(state, cfg)

    window.show()
    return application.exec()
