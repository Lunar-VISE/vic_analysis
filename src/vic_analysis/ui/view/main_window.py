from pathlib import Path

from PySide6.QtWidgets import QMainWindow

from vic_analysis.ui.view.main_view import MainView


class MainWindow(QMainWindow):
    """Top-level window for the VIC Analysis desktop application."""

    def __init__(self, main_view: MainView) -> None:
        super().__init__()
        self.setWindowTitle("VIC Analysis")
        self.setMinimumSize(1200, 900)

        self.home_directory = Path.cwd()

        self.main_view = main_view
        self.setCentralWidget(self.main_view)

        self._create_menus()

    def _create_menus(self) -> None:
        """Initializes menu actions."""
        file_menu = self.menuBar().addMenu("&File")

        set_home_directory_action = file_menu.addAction("Set Home Directory...")
        set_home_directory_action.triggered.connect(
            self.main_view.home_directory_change_requested.emit
        )

        open_action = file_menu.addAction("&Open...")
        open_action.triggered.connect(self.main_view.open_requested.emit)
