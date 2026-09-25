import numpy as np
from cmap import Colormap
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton, MouseEvent
from matplotlib.image import AxesImage
from matplotlib.patches import Polygon
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QSlider, QVBoxLayout, QWidget

from vic_analysis.numpy_dynamic_indexing import slice_along
from vic_analysis.ui.model.image_data import ImageData
from vic_analysis.ui.model.point_data import PointData
from vic_analysis.ui.view.widgets.lasso_selector import LassoSelector

from .widgets.zoom_canvas import ZoomCanvas


def no_nan(arr: np.ndarray) -> np.ndarray:
    return arr[np.isfinite(arr)]


class ImageView(QWidget):
    new_image_plotted: Signal = Signal()
    current_band_changed: Signal = Signal(int)
    single_pixel_clicked: Signal = Signal(PointData, MouseEvent)
    cursor_location_changed: Signal = Signal(PointData)
    released: Signal = Signal()

    def __init__(
        self, data: ImageData | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        # Define widgets
        self.canvas = ZoomCanvas(self)
        self.canvas.figure.set_facecolor((0, 0, 0, 0))

        self.sldr = QSlider(Qt.Orientation.Horizontal)
        self.sldr.setMinimum(0)
        self.sldr.setTickInterval(1)
        self.sldr.setMaximum(0)

        self.lasso_selector = LassoSelector(self.canvas)

        self.sldr.sliderMoved.connect(self.change_image_band)

        # Set widgets in layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addStretch()
        layout.addWidget(self.canvas)
        layout.addWidget(self.sldr)
        layout.addStretch()

        self.axes: Axes = self.canvas.axes
        self._init_axes()

        self.image: AxesImage = self.axes.imshow(
            np.full(
                (250, 250),
                fill_value=np.nan,
            ),
            aspect="equal",
        )
        self.axes.set_box_aspect(1)

        self._image_data: ImageData = ImageData.default()
        if data is not None:
            self._image_data = data

        self._current_slice = slice_along(
            self._image_data.array, 0, self._image_data.format.band_axis
        )

        self.pressed: bool = False

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.canvas.mpl_connect("button_release_event", self.on_release)

    def _init_axes(self):
        self.axes.set_xticks([])
        self.axes.set_yticks([])

    def plot_new_image(self) -> None:
        self.image.remove()
        img = slice_along(
            self._image_data.array,
            0,
            self._image_data.format.band_axis,
        )
        self._current_slice = img
        self.image: AxesImage = self.axes.imshow(img)
        self.axes.set_aspect("equal")
        self.new_image_plotted.emit()

    def change_image_band(self, band_index: int) -> None:
        """
        Slices the current image data array along band index and sets it as
        image data.
        """
        img = slice_along(
            self._image_data.array,
            band_index,
            self._image_data.format.band_axis,
        )
        self._current_slice = img
        self.image.set_data(img)
        self.update_color_limit()
        self.canvas.draw_idle()

        self.current_band_changed.emit(band_index)

    def update_color_limit(
        self, vmin: float | None = None, vmax: float | None = None
    ) -> None:
        if vmin is None or vmax is None:
            datavals = no_nan(self._current_slice)
            _vmin, _vmax = np.percentile(datavals, (5, 95))
            if vmin is None:
                vmin = _vmin
            if vmax is None:
                vmax = _vmax

        self.image.set_clim(vmin, vmax)

        self.canvas.draw_idle()

    def update_color_map(self, clrmap_name: str) -> None:
        clrmap = Colormap(clrmap_name).to_mpl()
        self.image.set_cmap(clrmap)

    def set_image_data(self, image_data: ImageData) -> None:
        print("IMAGE CHANGED IMAGE")
        self._image_data = image_data
        self.plot_new_image()
        self.update_color_limit()
        self.canvas.update_data_limits()
        self.canvas.update_plot()

        # Configure QSlider
        self.sldr.setMaximum(
            self._image_data.format.nbands(self._image_data.array.shape) - 1
        )

    def draw_polygon(self, poly: Polygon) -> None:
        self.axes.add_artist(poly)
        self.canvas.draw_idle()

    def on_press(self, event: MouseEvent) -> None:
        self.pressed = True
        match event.button:
            case MouseButton.LEFT:
                x = event.xdata
                y = event.ydata
                if x is None or y is None:
                    return

                ptdata = PointData(
                    float(x),
                    float(y),
                    int(round(x, 0)),
                    int(round(y, 0)),
                )
                self.single_pixel_clicked.emit(ptdata, event)

    def on_move(self, event: MouseEvent) -> None:
        x = event.xdata
        y = event.ydata
        if x is None or y is None:
            return

        ptdata = PointData(
            float(x),
            float(y),
            int(round(x, 0)),
            int(round(y, 0)),
        )

        self.cursor_location_changed.emit(ptdata)

    def on_release(self, event: MouseEvent) -> None:
        self.pressed = False
        self.released.emit()
