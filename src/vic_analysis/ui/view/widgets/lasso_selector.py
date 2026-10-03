from enum import Enum, auto

import numpy as np
from matplotlib.lines import Line2D
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QWidget

from vic_analysis.ui.model.lasso_selection import LassoSelection
from vic_analysis.ui.model.point_data import PointData
from vic_analysis.ui.view.widgets.matplotlib_canvas import MatplotlibCanvas


class LassoState(Enum):
    DRAWING = auto()
    IDLE = auto()


class LassoSelector(QWidget):
    lasso_started: Signal = Signal()
    lasso_finished: Signal = Signal(LassoSelection)
    lasso_canceled: Signal = Signal()

    def __init__(self, canvas: MatplotlibCanvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.state: LassoState = LassoState.IDLE

        self._lasso_vertices: list[tuple[float, float]] = []
        self._preview_line: Line2D | None = None
        self._preview_dirty = False
        self._preview_timer = QTimer(self)
        self._preview_timer.setInterval(10)
        self._preview_timer.timeout.connect(self._update_preview)

    def start_lasso(self, point_data: PointData) -> None:
        match self.state:
            case LassoState.DRAWING:
                return
            case LassoState.IDLE:
                self.state = LassoState.DRAWING
                self._lasso_vertices.append(point_data.point)
                (self._preview_line,) = self.canvas.axes.plot(
                    [point_data.x], [point_data.y], color="r"
                )
                self._preview_dirty = True
                self._preview_timer.start()
                self.lasso_started.emit()

    def lasso_movement(self, point_data: PointData) -> None:
        match self.state:
            case LassoState.IDLE:
                return
            case LassoState.DRAWING:
                self._lasso_vertices.append(point_data.point)
                self._preview_dirty = True

    def _update_preview(self) -> None:
        if not self._preview_dirty or self._preview_line is None:
            return

        self._preview_dirty = False
        vertices = np.asarray(self._lasso_vertices, dtype=np.float32)
        self._preview_line.set_data(vertices[:, 0], vertices[:, 1])
        self.canvas.draw_idle()

    def _remove_preview(self) -> None:
        self._preview_timer.stop()
        self._preview_dirty = False
        if self._preview_line is not None:
            self._preview_line.remove()
            self._preview_line = None
            self.canvas.draw_idle()

    def finish_lasso(self) -> None:
        match self.state:
            case LassoState.DRAWING:
                self.state = LassoState.IDLE

                verts = np.asarray(self._lasso_vertices, dtype=np.float32)
                self._lasso_vertices.clear()
                self._remove_preview()

                lasso_selection = LassoSelection(verts)
                self.lasso_finished.emit(lasso_selection)
            case LassoState.IDLE:
                return

    def cancel_lasso(self) -> None:
        match self.state:
            case LassoState.IDLE:
                return
            case LassoState.DRAWING:
                self.state = LassoState.IDLE
                self._lasso_vertices.clear()
                self._remove_preview()
                self.lasso_canceled.emit()
