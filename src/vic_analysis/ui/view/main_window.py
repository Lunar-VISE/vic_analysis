from pathlib import Path

from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtWidgets import QMainWindow

from vic_analysis.ui.controller.main_controller import MainController
from vic_analysis.ui.view.main_view import MainView


def get_screen(index: int = 0) -> QScreen:
    screens = QGuiApplication.screens()

    if not screens:
        raise RuntimeError("No screens are available.")

    index = max(0, min(index, len(screens) - 1))

    return screens[index]


class MainWindow(QMainWindow):
    """Top-level window for the VIC Analysis desktop application."""

    def __init__(self, main_view: MainView, main_controller: MainController) -> None:
        super().__init__()
        self.setWindowTitle("VIC Analysis")
        self.setMinimumSize(640, 640)

        self.home_directory = Path.cwd()

        self.main_view = main_view
        self.main_controller = main_controller

        self.setCentralWidget(self.main_view)

        self._create_menus()
        self._init_display()

    def _init_display(self) -> None:
        screen = get_screen(1)

        self.setGeometry(screen.geometry())
        self.showMaximized()

    def _create_menus(self) -> None:
        """Initializes menu actions."""
        file_menu = self.menuBar().addMenu("&File")

        set_home_directory_action = file_menu.addAction("Set Home Directory...")
        set_home_directory_action.triggered.connect(
            self.main_controller.change_home_directory
        )

        open_action = file_menu.addAction("&Open...")
        open_action.triggered.connect(self.main_controller.change_image)

        view_menu = self.menuBar().addMenu("&View")
        add_image_view_action = view_menu.addAction("New Image View")
        add_image_view_action.triggered.connect(self.main_controller.add_image_view)
