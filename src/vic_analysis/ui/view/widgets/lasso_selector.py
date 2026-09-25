from enum import Enum, auto

import numpy as np
from PySide6.QtCore import Signal
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
        self.canvas = canvas
        self.state: LassoState = LassoState.IDLE

        self._lasso_vertices: list[tuple[float, float]] = []

        super().__init__(canvas)

    def start_lasso(self, point_data: PointData) -> None:
        match self.state:
            case LassoState.DRAWING:
                return
            case LassoState.IDLE:
                print("Starting Lasso...")
                self.state = LassoState.DRAWING
                self._lasso_vertices.append(point_data.point)
                self.lasso_started.emit()

    def lasso_movement(self, point_data: PointData) -> None:
        match self.state:
            case LassoState.IDLE:
                return
            case LassoState.DRAWING:
                self._lasso_vertices.append(point_data.point)

    def finish_lasso(self) -> None:
        match self.state:
            case LassoState.DRAWING:
                self.state = LassoState.IDLE

                verts = np.asarray(self._lasso_vertices, dtype=np.float32)
                self._lasso_vertices.clear()

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
                self.lasso_canceled.emit()
