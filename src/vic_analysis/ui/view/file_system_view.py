from pathlib import Path

from PySide6.QtCore import QDir, QModelIndex, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileSystemModel,
    QHeaderView,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from vic_analysis.read.data_loader import file_suffix_list
from vic_analysis.ui.view.widgets.file_context_menu import FileContextMenu


class FileSystemView(QWidget):
    file_selected = Signal(Path)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.selection_menu = FileContextMenu("File System", self)

        self.model = QFileSystemModel()
        self.model.setFilter(
            QDir.Filter.AllDirs | QDir.Filter.Files | QDir.Filter.NoDotAndDotDot
        )
        self.model.setNameFilters([f"*{i}" for i in file_suffix_list])
        self.model.setNameFilterDisables(False)

        self.tree = self._init_tree()
        self.tree.selectionModel().currentChanged.connect(self._selection_changed)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)

        self.set_root_dir(Path.cwd())

    def set_root_dir(self, root_directory: Path) -> None:
        index = self.model.setRootPath(str(root_directory))
        self.tree.setRootIndex(index)

    def _init_tree(self) -> QTreeView:
        # === Initialization
        tree = QTreeView()
        tree.setModel(self.model)

        # === Aesthetics ===
        tree.setHeaderHidden(True)
        tree.setAnimated(True)
        tree.setIndentation(16)
        tree.setUniformRowHeights(True)
        for column in range(1, self.model.columnCount()):
            tree.hideColumn(column)

        # === Behavior ===
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        return tree

    def _selection_changed(self, current: QModelIndex, _previous: QModelIndex):
        # self.selection_menu.show()
        self.file_selected.emit(Path(self.model.filePath(current)))
