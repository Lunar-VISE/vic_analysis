from uuid import UUID, uuid4

import numpy as np
from cmap import Colormap
from matplotlib import patheffects
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton, MouseEvent, PickEvent
from matplotlib.collections import PathCollection
from matplotlib.image import AxesImage
from matplotlib.patches import Polygon
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtWidgets import QSlider, QVBoxLayout, QWidget

from vic_analysis.ui.model.artist_container import (
    ArtistCollection,
    PlottedArtist,
    make_scatter,
)
from vic_analysis.ui.model.image_data import ImageData
from vic_analysis.ui.model.plot_model import DataInputType, Plot, PlotModel
from vic_analysis.ui.model.point_data import PointData
from vic_analysis.ui.view.widgets.data_context_menu import DataContextMenu
from vic_analysis.ui.view.widgets.image_context_menu import ImageContextMenu
from vic_analysis.ui.view.widgets.lasso_selector import LassoSelector

from .widgets.zoom_canvas import ZoomCanvas, ZoomMode


def no_nan(arr: np.ndarray) -> np.ndarray:
    return arr[np.isfinite(arr)]


class ImageView(QWidget):
    new_image_plotted: Signal = Signal()
    current_band_changed: Signal = Signal(int)
    color_limits_changed: Signal = Signal(float, float)
    activated: Signal = Signal()
    single_pixel_clicked: Signal = Signal(PointData, MouseEvent)
    cursor_location_changed: Signal = Signal(PointData)
    released: Signal = Signal()

    def __init__(
        self,
        plot_model: PlotModel,
        data: ImageData | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.view_id = uuid4()
        self._plot_model = plot_model
        self._artist_collection = ArtistCollection()
        self.data_context_menu = DataContextMenu(self._plot_model, self)
        self.image_context_menu = ImageContextMenu(self._plot_model, self)

        # Define widgets
        self.canvas = ZoomCanvas(self, mode=ZoomMode.IMAGE)
        self.canvas.figure.set_frameon(True)
        self.canvas.figure.set_facecolor("#787878")

        self.sldr = QSlider(Qt.Orientation.Horizontal)
        self.sldr.setMinimum(0)
        self.sldr.setTickInterval(1)
        self.sldr.setMaximum(0)

        self.lasso_selector = LassoSelector(self.canvas)
        self.released.connect(self.lasso_selector.finish_lasso)

        self.sldr.sliderMoved.connect(self.change_image_band)

        # Set widgets in layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas)

        self.axes: Axes = self.canvas.axes
        self._init_axes()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(40)
        self._refresh_timer.timeout.connect(self._update_image_resolution)
        self.canvas.view_changed.connect(self._queue_image_update)

        self.image: AxesImage = self.axes.imshow(
            np.full(
                (250, 250),
                fill_value=np.nan,
            ),
            aspect="equal",
        )

        self._image_data: ImageData = ImageData.default()
        if data is not None:
            self._image_data = data

        self._current_band = 0

        self._hovered_artist: PathCollection | Polygon | None = None

        self.pressed: bool = False
        self._pick_active = False

        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_move)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("pick_event", self.on_pick)

        self._plot_model.plot_updated.connect(self._on_plot_update)
        self._plot_model.plot_removed.connect(self._remove_artist)
        self._plot_model.plot_hovered.connect(self._apply_path_effect)

    def _init_axes(self):
        # self.axes.set_facecolor("#A32727")
        self.axes.set_xticks([])
        self.axes.set_yticks([])

    def plot_new_image(self) -> None:
        self.image.remove()
        band_index = self._image_data.get_first_valid_band()
        self._current_band = band_index
        height = self._image_data.format.nrows(self._image_data.array.shape)
        width = self._image_data.format.ncols(self._image_data.array.shape)
        self.image: AxesImage = self.axes.imshow(
            np.full((1, 1), np.nan),
            aspect="equal",
            extent=(-0.5, width - 0.5, height - 0.5, -0.5),
        )
        self.axes.set_aspect("equal", adjustable="box")
        self.axes.relim()
        self.canvas.update_data_limits()
        self.canvas.update_plot()
        self._update_image_resolution()

        self.new_image_plotted.emit()
        self.current_band_changed.emit(band_index)

    def change_image_band(self, band_index: int) -> None:
        """
        Slices the current image data array along band index and sets it as
        image data.
        """
        self._current_band = band_index
        self._update_image_resolution()
        self.update_color_limit()
        self.canvas.draw_idle()
        self.current_band_changed.emit(band_index)

    def _queue_image_update(self) -> None:
        self._refresh_timer.start()

    def _update_image_resolution(self) -> None:
        if not hasattr(self, "_image_data"):
            return

        x_limits = self.axes.get_xlim()
        y_limits = self.axes.get_ylim()
        x_window = abs(x_limits[1] - x_limits[0])
        y_window = abs(y_limits[1] - y_limits[0])
        axes_bounds = self.axes.get_window_extent()
        if (
            x_window <= 0
            or y_window <= 0
            or axes_bounds.width <= 0
            or axes_bounds.height <= 0
        ):
            return

        pixels_per_source_pixel = min(
            axes_bounds.width / x_window,
            axes_bounds.height / y_window,
        )
        rows = self._image_data.format.nrows(self._image_data.array.shape)
        cols = self._image_data.format.ncols(self._image_data.array.shape)
        level_count = (
            self._image_data.pyramid.max_level
            if self._image_data.pyramid is not None
            else 0
        )
        level = min(
            level_count,
            max(0, int(np.floor(np.log2(1 / pixels_per_source_pixel)))),
        )
        factor = 2**level

        row_start = max(0, int(np.floor(min(y_limits) + 0.5)))
        row_stop = min(rows, int(np.ceil(max(y_limits) + 0.5)))
        col_start = max(0, int(np.floor(min(x_limits) + 0.5)))
        col_stop = min(cols, int(np.ceil(max(x_limits) + 0.5)))
        if row_start >= row_stop or col_start >= col_stop:
            image_data = np.full((1, 1), np.nan)
            extent = (-0.5, 0.5, 0.5, -0.5)
        else:
            level_row_start = row_start // factor
            level_row_stop = (row_stop + factor - 1) // factor
            level_col_start = col_start // factor
            level_col_stop = (col_stop + factor - 1) // factor
            if level == 0 or self._image_data.pyramid is None:
                image_data = self._image_data.read_window(
                    self._current_band,
                    row_start,
                    row_stop,
                    col_start,
                    col_stop,
                )
            else:
                image_data = self._image_data.pyramid.read_region(
                    self._current_band,
                    level,
                    level_row_start,
                    level_row_stop,
                    level_col_start,
                    level_col_stop,
                )
            extent = (
                level_col_start * factor - 0.5,
                min(level_col_stop * factor, cols) - 0.5,
                min(level_row_stop * factor, rows) - 0.5,
                level_row_start * factor - 0.5,
            )

        self.image.set_data(image_data)
        self.image.set_extent(extent)
        self.canvas.draw_idle()

    def update_color_limit(
        self, vmin: float | None = None, vmax: float | None = None
    ) -> None:
        if vmin is None or vmax is None:
            datavals = no_nan(self._image_data.sample_band(self._current_band))
            _vmin, _vmax = np.percentile(datavals, (5, 95))
            if vmin is None:
                vmin = _vmin
            if vmax is None:
                vmax = _vmax

        self.image.set_clim(vmin, vmax)
        self.color_limits_changed.emit(*self.image.get_clim())

        self.canvas.draw_idle()

    def update_color_map(self, clrmap_name: str) -> None:
        clrmap = Colormap(clrmap_name).to_mpl()
        self.image.set_cmap(clrmap)

    def set_image_data(self, image_data: ImageData) -> None:
        self._image_data = image_data
        self.plot_new_image()
        self.update_color_limit()

        # Configure QSlider
        self.sldr.setMaximum(
            self._image_data.format.nbands(self._image_data.array.shape) - 1
        )

    def on_press(self, event: MouseEvent) -> None:
        if self._pick_active:
            self._pick_active = False
            return
        self.activated.emit()
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
            case MouseButton.RIGHT:
                self.image_context_menu.popup(self._get_global_position(event))

    def on_move(self, event: MouseEvent) -> None:
        self._on_hover(event)
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

    def on_pick(self, event: PickEvent) -> None:
        self._pick_active = True
        mouse_event = event.mouseevent
        pos = self._get_global_position(mouse_event)
        match mouse_event.button:
            case MouseButton.RIGHT:
                plotted_art = self._artist_collection.get_artist(event.artist)
                self.data_context_menu.popup(plotted_art.id, pos)
            case _:
                return

    def on_release(self, event: MouseEvent) -> None:
        self.pressed = False
        self.released.emit()

    def _create_poly(self, plot: Plot) -> Polygon:
        poly = Polygon(np.zeros((0, 2)), facecolor=plot.color, edgecolor="k", picker=5)
        plt_art = PlottedArtist(poly, plot.color, plot.id)
        self._artist_collection.add_plotted_artist(plt_art)
        return poly

    def _create_scatter(self, plot: Plot) -> PathCollection:
        scatter = make_scatter(
            self.axes,
            size=50,
            marker="x",
            color=plot.color.rgba,
        )
        plt_art = PlottedArtist(scatter, plot.color, plot.id)
        self._artist_collection.add_plotted_artist(plt_art)
        return scatter

    def _create_artist(self, plot: Plot) -> None:
        artist: Polygon | PathCollection
        if plot.data.is_point:
            artist = self._create_scatter(plot)
        else:
            artist = self._create_poly(plot)
        self.axes.add_artist(artist)
        self.canvas.draw_idle()

    def _on_plot_update(self, id: UUID, data_input_type: DataInputType) -> None:
        if data_input_type != DataInputType.PIXEL:
            return

        plot = self._plot_model.get_plot_from_id(id)

        if not self._artist_collection.check_id(id):
            self._create_artist(plot)

        artist = self._artist_collection.get_id(id).art
        if isinstance(artist, Polygon):
            artist.set_xy(plot.data.require_pixel())
        elif isinstance(artist, PathCollection):
            artist.set_offsets(plot.data.require_pixel())
        else:
            raise TypeError(f"Invalid artist type: {artist}")

    def _remove_artist(self, id) -> None:
        art = self._artist_collection.get_id(id)
        self._artist_collection.remove_plotted_artist(art)
        self.canvas.draw_idle()

    def _get_global_position(self, mouse_event: MouseEvent) -> QPoint:
        canvas_position = QPoint(
            int(mouse_event.x), self.canvas.height() - int(mouse_event.y)
        )
        global_position = self.mapToGlobal(canvas_position)
        return global_position

    def _on_hover(self, event: MouseEvent) -> None:
        if event.inaxes is not self.axes:
            return

        # === Detect Which Artist is being Hovered Over ===
        hovered_artist = next(
            (
                art
                for art in self.axes.get_children()
                if art.contains(event)[0] and isinstance(art, (PathCollection, Polygon))
            ),
            None,
        )

        # === Detecting end of hover ===
        if (hovered_artist is None) and (self._hovered_artist is not None):
            id = self._artist_collection.get_artist(self._hovered_artist).id
            self._plot_model.plot_hovered.emit(id, False)
            self._hovered_artist = None

        # === Detecting start of hover ===
        if (hovered_artist is not None) and (self._hovered_artist is None):
            id = self._artist_collection.get_artist(hovered_artist).id
            self._plot_model.plot_hovered.emit(id, True)
            self._hovered_artist = hovered_artist

    def _apply_path_effect(self, id: UUID, hover_on: bool) -> None:
        hovered_artist = self._artist_collection.get_id(id).art
        if hover_on:
            hovered_artist.set_path_effects(
                [
                    patheffects.Stroke(linewidth=6, foreground="red"),
                    patheffects.Normal(),
                ]
            )
        else:
            hovered_artist.set_path_effects([])
        self.canvas.draw_idle()
