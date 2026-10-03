from PySide6.QtWidgets import (
    QMenu,
    QWidget,
)


class ImageViewMenu(QMenu):
    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)


class FileContextMenu(QMenu):
    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)

        self.image_view_menu = ImageViewMenu("View in Existing Image Frame...", self)
        self.addMenu(self.image_view_menu)
