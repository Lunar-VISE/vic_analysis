from cmath import isinf
from dataclasses import dataclass
from typing import Self

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import cursors
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QMoveEvent, QWheelEvent
from PySide6.QtWidgets import QWidget

from .matplotlib_canvas import MatplotlibCanvas


@dataclass
class Point:
    x: float
    y: float

    def __sub__(self, other: Self) -> Self:
        return self.__class__(x=self.x - other.x, y=self.y - other.y)

    def __add__(self, other: Self) -> Self:
        return self.__class__(x=self.x + other.x, y=self.y + other.y)


def get_fig_coords(
    display_coords: np.ndarray, fig_height: float, fig_width: float
) -> np.ndarray:
    fig_y = 1 - (display_coords[0] / fig_height)
    fig_x = display_coords[1] / fig_width
    fig_coords = np.array([fig_y, fig_x])
    return fig_coords


def screen_coords_to_data_coords(
    screen_coords: np.ndarray,
    fig_height: float,
    fig_width: float,
    figure: Figure,
    axes: Axes,
) -> np.ndarray:
    """
    Transforms from screen coordinates given by mouse events, for example, into
    data coordinates on a given axis and figure.
    """
    fig_coords = get_fig_coords(screen_coords, fig_height, fig_width)
    data_coords = axes.transData.inverted().transform(
        figure.transFigure.transform(fig_coords[::-1])
    )
    return data_coords


class ZoomCanvas(MatplotlibCanvas):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.axes: Axes = self.axes

        self.update_data_limits()

        self.fig_width, self.fig_height = self.get_width_height()

        self.is_panning = False

    def update_data_limits(self) -> None:
        self._starting_data_limits: Bbox = self.axes.dataLim

        if any(isinf(i) for i in self._starting_data_limits.bounds):
            self.center = Point(0, 0)
            self.x_window = 5
            self.y_window = 5
            self._starting_window = 5
            return

        x_center = (
            self._starting_data_limits.xmax + self._starting_data_limits.xmin
        ) / 2
        y_center = (
            self._starting_data_limits.ymax + self._starting_data_limits.ymin
        ) / 2

        self.center = Point(x_center, y_center)
        self._starting_window = max(self._starting_data_limits.bounds[2:])
        self.x_window = self._starting_window
        self.y_window = self._starting_window

    def update_plot(self) -> None:
        x_left = self.center.x - self.x_window / 2
        x_right = self.center.x + self.x_window / 2

        y_bot = self.center.y - self.y_window / 2
        y_top = self.center.y + self.y_window / 2

        self.axes.set_xlim(x_left, x_right)
        self.axes.set_ylim(y_top, y_bot)

        self.draw_idle()

    def zoom_x(self, factor: float) -> None:
        self.x_window *= factor
        self.x_window = np.clip(self.x_window, 1, self._starting_window)

        self.update_plot()

    def zoom_y(self, factor: float) -> None:
        self.y_window *= factor
        self.y_window = np.clip(self.y_window, 1, self._starting_window)

        self.update_plot()

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()

        if delta == 0:
            return

        if delta > 0:
            factor = 0.9
        else:
            factor = 1.1

        self.zoom_x(factor)
        self.zoom_y(factor)
        self.fig_height_width = np.array(self.get_width_height())[::-1]
        return super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        bttn = event.button()

        if bttn == Qt.MouseButton.MiddleButton:
            screen_coords = np.array((event.position().y(), event.position().x()))
            self._pan_start = screen_coords_to_data_coords(
                screen_coords,
                self.fig_height,
                self.fig_width,
                self.figure,
                self.axes,
            )

            self.set_cursor(cursors.HAND)

            self.is_panning = True

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMoveEvent):
        if self.is_panning:
            display_coords = np.array(
                (event.position().y(), event.position().x())  # type: ignore
            )
            data_coords = screen_coords_to_data_coords(
                display_coords,
                self.fig_height,
                self.fig_width,
                self.figure,
                self.axes,
            )

            diff_coords = self._pan_start - data_coords

            self.center += Point(x=diff_coords[0], y=diff_coords[1])

            self.update_plot()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        bttn = event.button()

        if bttn == Qt.MouseButton.MiddleButton:
            self.set_cursor(cursors.POINTER)
            self.is_panning = False
        return super().mouseReleaseEvent(event)
