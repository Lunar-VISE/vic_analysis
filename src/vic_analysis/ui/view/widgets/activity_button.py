from uuid import uuid4

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QToolButton, QWidget

from vic_analysis.ui.model.button_name import ButtonName


class ActivityButton(QToolButton):
    activated = Signal()

    def __init__(
        self, name: ButtonName = ButtonName.DEFAULT, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self.name = name
        self._id = uuid4()

        self.setCheckable(True)
        self.setAutoRaise(True)

        self.clicked.connect(self.activated)

    def __eq__(self, other: object) -> bool:
        """Buttons have matching UUIDs"""
        if not isinstance(other, ActivityButton):
            return NotImplemented
        return self._id == self._id and self.name == self.name

    def __hash__(self):
        """Combine attributes into a tuple and hash it"""
        return hash((self._id, self.name))
