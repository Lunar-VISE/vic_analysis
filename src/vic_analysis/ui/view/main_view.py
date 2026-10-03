from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QWidget,
)
from PySide6QtAds import CDockManager, CDockWidget, DockWidgetArea

from vic_analysis.read.stylesheet import QTADS_STYLE, load_stylesheet
from vic_analysis.ui.view.activity_bar import ActivityBar
from vic_analysis.ui.view.file_system_view import FileSystemView
from vic_analysis.ui.view.hisotgram_view import HistogramView
from vic_analysis.ui.view.image_view import ImageView
from vic_analysis.ui.view.spectral_view import SpectralView


class MainView(QWidget):
    """Top-level window for the VIC Analysis desktop application."""

    def __init__(
        self,
        activity_bar: ActivityBar,
        image_view: ImageView,
        spectral_view: SpectralView,
        histogram_view: HistogramView,
        file_system_view: FileSystemView,
    ) -> None:
        super().__init__()

        self.dock_manager = self._make_dock_manager()
        self.activity_bar = activity_bar

        self.image_view = image_view
        self.image_docks: list[CDockWidget] = []
        self.spectral_view = spectral_view
        self.histogram_view = histogram_view
        self.file_system_view = file_system_view

        self.image_dock = self.add_image_view(self.image_view)

        self.spectral_dock = self._make_dock(
            "Spectral", self.spectral_view, DockWidgetArea.RightDockWidgetArea
        )

        self.histogram_dock = self._make_dock(
            "Histogram",
            self.histogram_view,
            DockWidgetArea.LeftDockWidgetArea,
            start_closed=True,
        )

        self.file_system_dock = self._make_dock(
            "Files",
            self.file_system_view,
            DockWidgetArea.LeftDockWidgetArea,
            start_closed=True,
        )

        self._build_ui()

    def choose_image_file(self, current_home_directory: Path) -> Path:
        """
        Opens a file dialog for selecting a compatible image.
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image Data",
            str(current_home_directory),
            "Cubio JSON (*.json);;VIC Binary (*.bin);;ENVI Compatible (*.bsq *.bil *.bip)",
        )

        if not path:
            raise ValueError("No path selected.")

        return Path(path)

    def choose_home_directory(self, current_home_directory: Path) -> Path:
        """
        Opens a file dialog to select a directory.
        """
        path = QFileDialog.getExistingDirectory(
            self, "Select New Home Directory", str(current_home_directory)
        )
        if not path:
            raise ValueError("No path selected.")
        return Path(path)

    def choose_save_directory(self, current_home_directory: Path) -> Path:
        path = QFileDialog.getExistingDirectory(
            self, "Select Save Directory", str(current_home_directory)
        )
        if not path:
            raise ValueError("No path selected.")
        return Path(path)

    def add_image_view(self, image_view: ImageView) -> CDockWidget:
        dock_number = len(self.image_docks) + 1
        title = "Image" if dock_number == 1 else f"Image {dock_number}"
        dock = self._make_dock(title, image_view, DockWidgetArea.CenterDockWidgetArea)
        self.image_docks.append(dock)
        return dock

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.activity_bar)
        layout.addWidget(self.dock_manager)

    def _make_dock(
        self,
        title: str,
        widget: QWidget,
        area: DockWidgetArea,
        start_closed: bool = False,
    ) -> CDockWidget:
        dock = CDockWidget(title)
        dock.setWidget(widget)

        self.dock_manager.addDockWidget(area, dock)

        if start_closed:
            dock.toggleView(False)

        return dock

    def _make_dock_manager(self) -> CDockManager:
        manager = CDockManager(self)

        manager.setStyleSheet(load_stylesheet(QTADS_STYLE))
        return manager
