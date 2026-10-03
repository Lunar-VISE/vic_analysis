from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QWidget


class MatplotlibCanvas(FigureCanvasQTAgg):
    def __init__(
        self, parent: QWidget | None = None, remove_boundaries: bool = True
    ) -> None:
        self.figure = Figure(frameon=False)
        super().__init__(self.figure)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if parent is not None:
            self.setParent(parent)

        if remove_boundaries:
            self.axes: Axes = self.figure.add_axes((0, 0, 1, 1))
            self.axes.set_axis_off()
            self.axes.set_box_aspect(None)
            self.figure.subplots_adjust(left=0, right=1, bottom=0, top=1)
        else:
            self.axes = self.figure.add_subplot(111)

        self.draw_idle()
