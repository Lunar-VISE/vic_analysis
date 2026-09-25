from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QSizePolicy, QWidget


class MatplotlibCanvas(FigureCanvasQTAgg):
    def __init__(self, parent: QWidget | None = None) -> None:
        self.figure = Figure()
        super().__init__(self.figure)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if parent is not None:
            self.setParent(parent)

        self.axes: Axes = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0, right=1, bottom=0, top=1)

        self.draw_idle()
