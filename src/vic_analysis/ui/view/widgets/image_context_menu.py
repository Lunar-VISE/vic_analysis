from PySide6.QtCore import QObject, QPoint, Signal
from PySide6.QtWidgets import QMenu, QWidget

from vic_analysis.ui.model.plot_model import PlotModel


class ImageContextMenu(QObject):
    delete_all_requested = Signal()
    save_all_requested = Signal()
    save_group_requested = Signal()

    def __init__(self, plot_model: PlotModel, parent: QWidget) -> None:
        super().__init__(parent)
        self.menu = QMenu(parent)
        self._plot_model = plot_model

        self.delete_all_action = self.menu.addAction("Delete All")
        self.delete_all_action.triggered.connect(self._on_delete_all)

        self.save_all_action = self.menu.addAction("Save All")
        self.save_all_action.triggered.connect(self._on_save_all)

        self.save_group_action = self.menu.addAction("Save as Group")
        self.save_group_action.triggered.connect(self._on_save_group)

    def popup(self, position: QPoint) -> None:
        self.menu.popup(position)

    def _on_delete_all(self) -> None:
        self._plot_model.reset()
        self.delete_all_requested.emit()

    def _on_save_all(self) -> None:
        self.save_all_requested.emit()

    def _on_save_group(self) -> None:
        self.save_group_requested.emit()
