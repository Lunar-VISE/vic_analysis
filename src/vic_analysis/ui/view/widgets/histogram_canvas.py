from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from .matplotlib_canvas import MatplotlibCanvas


class HistogramCanvas(MatplotlibCanvas):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_start: tuple[float, float] | None = None
        self._pan_start: tuple[float, float] | None = None
        self._pan_limits: tuple[float, float] | None = None

    def mousePressEvent(self, event: QMouseEvent) -> None:
        x = event.position().x()
        y = event.position().y()

        match event.button():
            case Qt.MouseButton.RightButton:
                self._drag_start = (event.position().x(), event.position().y())
                event.accept()
                return
            case Qt.MouseButton.MiddleButton:
                self._pan_start = (x, y)
                self._pan_limits = self.axes.get_ylim()
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None:
            self._zoom_from_drag(event)
            event.accept()
            return

        if self._pan_start is not None:
            self._pan_from_drag(event)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        match event.button():
            case Qt.MouseButton.RightButton:
                self._drag_start = None
                event.accept()
                return
            case Qt.MouseButton.MiddleButton:
                self._pan_start = None
                self._pan_limits = None
                event.accept()
                return

        super().mouseReleaseEvent(event)

    def _pan_from_drag(self, event: QMouseEvent) -> None:
        if self._pan_start is None or self._pan_limits is None:
            return

        _start_x, start_y = self._pan_start

        current_y = event.position().y()

        dy = current_y - start_y

        ymin, ymax = self._pan_limits

        yscale = (ymax - ymin) / self.height()

        self.axes.set_ylim(ymin + dy * yscale, ymax + dy * yscale)

        self.draw_idle()

    def _zoom_from_drag(self, event: QMouseEvent) -> None:
        _start_x, start_y = self._drag_start

        current_x = event.position().x()
        current_y = event.position().y()

        dy = current_y - start_y

        if abs(dy) > 100:
            return

        self._zoom_y(current_x, current_y, dy)

    def _zoom_y(self, pixel_x: float, pixel_y: float, delta: float) -> None:
        _, y = self._pixel_to_data(pixel_x, pixel_y)
        ymin, ymax = self.axes.get_ylim()
        height = ymax - ymin

        scale = 1.0 + delta / self.height()
        scale = max(0.1, min(scale, 10.0))

        new_height = height * scale

        fraction = (y - ymin) / height

        new_ymin = y - fraction * new_height
        new_ymax = new_ymin + new_height

        self.axes.set_ylim(new_ymin, new_ymax)
        self.draw_idle()

    def _pixel_to_data(self, pixel_x: float, pixel_y: float) -> tuple[float, float]:
        height = self.height()

        mpl_x = pixel_x
        mpl_y = height - pixel_y

        return self.axes.transData.inverted().transform((mpl_x, mpl_y))
