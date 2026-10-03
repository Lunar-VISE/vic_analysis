from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QVBoxLayout, QWidget

from vic_analysis.resources import resources_rc  # noqa: F401
from vic_analysis.ui.model.button_name import TOOLTIP_DICT, ButtonName
from vic_analysis.ui.view.widgets.activity_button import ActivityButton


class ActivityBar(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.group = QButtonGroup()
        self.group.setExclusive(False)

        self._layout = QVBoxLayout(self)

        self.folder = self._make_button(
            ButtonName.FOLDER, QIcon(":/icons/folder_symbol.svg")
        )
        self.histogram = self._make_button(
            ButtonName.HISTOGRAM, QIcon(":/icons/histogram.svg")
        )

        self._layout.addStretch()

    def _make_button(self, name: ButtonName, icon: QIcon) -> ActivityButton:
        button = ActivityButton(name)

        button.setFixedSize(48, 48)
        button.setObjectName(name)
        button.setIcon(icon)
        button.setIconSize(QSize(48, 48))
        button.setToolTip(TOOLTIP_DICT.get(name, "Tooltip Not Set..."))

        self._layout.addWidget(button)
        self.group.addButton(button)

        return button
