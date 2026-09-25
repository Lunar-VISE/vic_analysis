from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QWidget,
)

from vic_analysis.ui.view.hisotgram_view import HistogramView
from vic_analysis.ui.view.image_view import ImageView


class MainView(QWidget):
    """Top-level window for the VIC Analysis desktop application."""

    open_requested = Signal()
    home_directory_change_requested = Signal()

    def __init__(self, image_view: ImageView, histogram_view: HistogramView) -> None:
        super().__init__()

        self.home_directory = Path.cwd()
        self.image_view = image_view
        self.histogram_view = histogram_view

        self._build_ui()

    def choose_image_file(self) -> Path:
        """
        Opens a file dialog for selecting a compatible image.
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image Data",
            str(self.home_directory),
            "Cubio JSON (*.json);;VIC Binary (*.bin);;ENVI Compatible (*.bsq *.bil *.bip)",
        )

        if not path:
            raise ValueError("No path selected.")
        return Path(path)

    def choose_home_directory(self) -> Path:
        """
        Opens a file dialog to select a directory.
        """
        path = QFileDialog.getExistingDirectory(
            self, "Select New Home Directory", str(self.home_directory)
        )
        if not path:
            raise ValueError("No path selected.")
        return Path(path)

    def update_home_directory(self, filepath: Path) -> None:
        self.home_directory = filepath

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addStretch()
        layout.addWidget(self.image_view)
        layout.addWidget(self.histogram_view)
        layout.addStretch()

        # self.image_view.canvas.mpl_connect("draw_event", self._sync_histogram_height)

    # def _sync_histogram_height(self, event=None) -> None:
    #     axes_height = self.image_view.axes.get_position().height
    #     canvas_height = self.image_view.canvas.height()
    #     self.histogram_view.setFixedHeight(round(axes_height * canvas_height))
