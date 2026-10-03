from uuid import UUID

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QInputDialog, QMenu, QWidget

from vic_analysis.ui.model.plot_model import PlotModel


class DataContextMenu:
    def __init__(self, plot_model: PlotModel, parent: QWidget) -> None:
        self.menu = QMenu(parent)
        self.plot_model = plot_model

        self._id: UUID | None = None

        self.rename_action = self.menu.addAction("Rename")
        self.rename_action.triggered.connect(self._on_rename)

        self.delete_action = self.menu.addAction("Delete")
        self.delete_action.triggered.connect(self._on_delete)

    def popup(self, id: UUID, position: QPoint) -> None:
        self._id = id
        self.menu.popup(position)

    def _on_delete(self) -> None:
        if self._id is not None:
            self.plot_model.remove_plot(self._id)

    def _on_rename(self) -> None:
        if self._id is None:
            return
        text, ok = QInputDialog.getText(
            self.menu, "Plot Renaming", "Enter a new plot name..."
        )
        if ok:
            self.plot_model.rename_plot(self._id, text)
