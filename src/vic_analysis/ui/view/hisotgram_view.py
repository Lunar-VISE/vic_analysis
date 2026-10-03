import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton, MouseEvent, PickEvent
from matplotlib.container import BarContainer
from matplotlib.lines import Line2D
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from vic_analysis.ui.view.widgets.histogram_canvas import HistogramCanvas


class HistogramView(QWidget):
    color_limits_change_requested: Signal = Signal(float, float)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.canvas = HistogramCanvas()
        self.canvas.figure.set_facecolor((0, 0, 0, 0))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.axes: Axes = self.canvas.axes

        self._init_axes()

        self.setFixedWidth(100)

        self._drag_artist: Line2D | None = None
        self._dragging: bool = False

        self.hist_line: Line2D | None = None
        self.min_line: Line2D | None = None
        self.max_line: Line2D | None = None
        self.hist_fill: BarContainer | None = None

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("pick_event", self.on_pick)
        self.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.canvas.mpl_connect("button_release_event", self.on_release)

    def _init_axes(self):
        self.axes.set_xticks([])
        self.axes.set_yticks([])

    def _reset_plot(self) -> None:
        for i in [self.hist_line, self.min_line, self.max_line, self.hist_fill]:
            if i is None:
                continue
            i.remove()
        self.axes.relim()
        self.axes.autoscale()

    def draw_new_histogram(self, clean_data: np.ndarray) -> None:
        self._reset_plot()
        hist, bins = np.histogram(clean_data, bins=500, density=True)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        bin_widths = (bin_centers.max() - bin_centers.min()) / len(bin_centers)
        self._current_bins = bin_centers
        (self.hist_line,) = self.axes.step(hist, bin_centers, where="pre", color="k")
        self.hist_fill = self.axes.barh(bin_centers, hist, bin_widths, align="edge")

        vmin, vmax, ymin, ymax = np.percentile(clean_data, (5, 95, 0.5, 99.5))

        self.min_line = self.axes.axhline(vmin, color="r", picker=5)
        self.max_line = self.axes.axhline(vmax, color="r", picker=5)

        clims = (vmin, vmax)
        self.update_histogram(clims)

        self.axes.set_ylim(ymin, ymax)

        self.canvas.draw_idle()

    def update_histogram(self, color_limits: tuple[float, float]):
        if self.hist_fill is None:
            return
        in_limits = (self._current_bins >= color_limits[0]) * (
            self._current_bins <= color_limits[1]
        )
        fill_colors = [(1, 0, 0, 0.4) if i else (0, 0, 0, 0) for i in in_limits]
        for bar, clr in zip(self.hist_fill, fill_colors):
            bar.set_facecolor(clr)

        self.canvas.draw_idle()

    def on_pick(self, event: PickEvent) -> None:
        if not isinstance(event.artist, Line2D):
            return
        mouse = event.mouseevent
        match mouse.button:
            case MouseButton.LEFT:
                self._drag_artist = event.artist

    def on_press(self, event: MouseEvent) -> None:
        if self._drag_artist is not None:
            self._dragging = True

    def on_drag(self, event: MouseEvent) -> None:
        if self._drag_artist is None or not self._dragging:
            return
        y = event.ydata
        if y is None:
            return
        self._drag_artist.set_ydata([y, y])
        self.canvas.draw_idle()

    def on_release(self, event: MouseEvent) -> None:
        if self.min_line is None or self.max_line is None:
            return
        if self._dragging:
            vmin = self.min_line.get_ydata()
            vmax = self.max_line.get_ydata()
            if not isinstance(vmin, list) or not isinstance(vmax, list):
                return
            self.color_limits_change_requested.emit(float(vmin[0]), float(vmax[0]))
        self._dragging = False
