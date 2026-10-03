from dataclasses import dataclass
from enum import Enum, auto
from typing import Self

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import cursors
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QResizeEvent, QWheelEvent
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


class ZoomMode(Enum):
    IMAGE = auto()
    PLOT = auto()


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
    view_changed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        remove_boundaries: bool = True,
        *,
        mode: ZoomMode = ZoomMode.IMAGE,
    ) -> None:
        super().__init__(parent, remove_boundaries)

        self.mode = mode
        self.axes: Axes = self.axes

        self.update_data_limits()

        self.fig_width, self.fig_height = self.get_width_height()

        self.is_panning = False
        self._right_zoom_start: tuple[float, float] | None = None
        self._right_zoom_anchor: np.ndarray | None = None
        self._right_zoom_start_xlim: tuple[float, float] | None = None
        self._right_zoom_start_ylim: tuple[float, float] | None = None
        self._right_zoom_axis: str | None = None
        self._right_zoom_start_x_window = 0.0
        self._right_zoom_start_y_window = 0.0
        self.right_dragged = False

    def update_data_limits(self) -> None:
        self._starting_data_limits: Bbox = self.axes.dataLim

        if not np.isfinite(self._starting_data_limits.bounds).all():
            self.center = Point(0, 0)
            self.x_window = 5
            self.y_window = 5
            self._starting_x_window = 5
            self._starting_y_window = 5
            return

        x_center = (
            self._starting_data_limits.xmax + self._starting_data_limits.xmin
        ) / 2
        y_center = (
            self._starting_data_limits.ymax + self._starting_data_limits.ymin
        ) / 2

        self.center = Point(x_center, y_center)
        self.x_window = self._starting_data_limits.bounds[2]
        self.y_window = self._starting_data_limits.bounds[3]
        self._starting_x_window = self.x_window
        self._starting_y_window = self.y_window

    def update_plot(self) -> None:
        canvas_width, canvas_height = self.get_width_height()
        if canvas_width <= 0 or canvas_height <= 0:
            return

        if self.mode is ZoomMode.IMAGE:
            aspect_ratio = canvas_width / canvas_height
            visible_x_window = min(self.x_window, self.y_window * aspect_ratio)
            visible_y_window = visible_x_window / aspect_ratio

            self.axes.set_xlim(
                self.center.x - visible_x_window / 2,
                self.center.x + visible_x_window / 2,
            )
            self.axes.set_ylim(
                self.center.y + visible_y_window / 2,
                self.center.y - visible_y_window / 2,
            )
        else:
            self.axes.set_xlim(
                self.center.x - self.x_window / 2,
                self.center.x + self.x_window / 2,
            )
            self.axes.set_ylim(
                self.center.y - self.y_window / 2,
                self.center.y + self.y_window / 2,
            )

        self.draw_idle()
        self.view_changed.emit()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.fig_width, self.fig_height = self.get_width_height()
        if hasattr(self, "x_window"):
            self.update_plot()

    def zoom_x(self, factor: float) -> None:
        self.x_window *= factor
        min_window = self._min_window(self._starting_x_window)
        self.x_window = np.clip(self.x_window, min_window, None)

        self.update_plot()

    def zoom_y(self, factor: float) -> None:
        self.y_window *= factor
        min_window = self._min_window(self._starting_y_window)
        self.y_window = np.clip(self.y_window, min_window, None)

        self.update_plot()

    def _min_window(self, starting_window: float) -> float:
        if self.mode is ZoomMode.IMAGE:
            return min(1, starting_window)
        return max(starting_window * 1e-6, np.finfo(float).eps)

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

        if bttn == Qt.MouseButton.RightButton and self.mode is ZoomMode.PLOT:
            position = event.position()
            self._right_zoom_start = (position.x(), position.y())
            self._right_zoom_anchor = screen_coords_to_data_coords(
                np.array((position.y(), position.x())),
                self.fig_height,
                self.fig_width,
                self.figure,
                self.axes,
            )
            self._right_zoom_start_xlim = self.axes.get_xlim()
            self._right_zoom_start_ylim = self.axes.get_ylim()
            self._right_zoom_start_x_window = self.x_window
            self._right_zoom_start_y_window = self.y_window
            self._right_zoom_axis = None
            self.right_dragged = False

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

    def mouseMoveEvent(self, event: QMouseEvent):
        if (
            self._right_zoom_start is not None
            and event.buttons() & Qt.MouseButton.RightButton
        ):
            self._zoom_from_right_drag(event)

        if self.is_panning:
            display_coords = np.array((event.position().y(), event.position().x()))
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

        right_zoom_release = (
            bttn == Qt.MouseButton.RightButton and self._right_zoom_start is not None
        )
        if right_zoom_release:
            self._right_zoom_start = None
            self._right_zoom_anchor = None
            self._right_zoom_start_xlim = None
            self._right_zoom_start_ylim = None
            self._right_zoom_axis = None

        if bttn == Qt.MouseButton.MiddleButton:
            self.set_cursor(cursors.POINTER)
            self.is_panning = False

        result = super().mouseReleaseEvent(event)
        if right_zoom_release:
            self.right_dragged = False
        return result

    def _zoom_from_right_drag(self, event: QMouseEvent) -> None:
        if (
            self._right_zoom_start is None
            or self._right_zoom_anchor is None
            or self._right_zoom_start_xlim is None
            or self._right_zoom_start_ylim is None
        ):
            return

        start_x, start_y = self._right_zoom_start
        delta_x = event.position().x() - start_x
        delta_y = event.position().y() - start_y

        if self._right_zoom_axis is None:
            if max(abs(delta_x), abs(delta_y)) < 3:
                return
            self._right_zoom_axis = "x" if abs(delta_x) >= abs(delta_y) else "y"

        self.right_dragged = True
        if self._right_zoom_axis == "x":
            factor = np.clip(1 + delta_x / max(self.fig_width, 1), 0.1, 10)
            window = np.clip(
                self._right_zoom_start_x_window * factor,
                self._min_window(self._starting_x_window),
                self._starting_x_window * 10,
            )
            limits = self._right_zoom_start_xlim
            anchor = self._right_zoom_anchor[0]
            fraction = (anchor - limits[0]) / (limits[1] - limits[0])
            self.x_window = window
            self.center.x = anchor + (0.5 - fraction) * window
        else:
            factor = np.clip(1 + delta_y / max(self.fig_height, 1), 0.1, 10)
            window = np.clip(
                self._right_zoom_start_y_window * factor,
                self._min_window(self._starting_y_window),
                self._starting_y_window * 10,
            )
            limits = self._right_zoom_start_ylim
            anchor = self._right_zoom_anchor[1]
            fraction = (anchor - limits[0]) / (limits[1] - limits[0])
            self.y_window = window
            self.center.y = anchor + (0.5 - fraction) * window

        self.update_plot()
