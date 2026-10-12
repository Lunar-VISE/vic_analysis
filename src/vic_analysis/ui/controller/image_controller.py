from matplotlib.backend_bases import KeyEvent, MouseEvent

from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.model.image_data import ImageData
from vic_analysis.ui.model.lasso_selection import LassoSelection
from vic_analysis.ui.model.plot_model import DataInputType, PlotModel
from vic_analysis.ui.model.point_data import PointData
from vic_analysis.ui.model.spatial_data import SpatialData, spatial_data_adapter
from vic_analysis.ui.view.image_view import ImageView


class ImageController:
    def __init__(self, plot_model: PlotModel, view: ImageView, state: AppState) -> None:
        self.state = state
        self.view = view
        self._plot_model = plot_model
        view_state = self.state.register_image_view(self.view.view_id)

        # State Slots
        self.state.image_changed.connect(self._on_image_change)
        self.state.colormap_changed.connect(self._on_color_map_change)
        self.state.color_limits_changed.connect(self._on_color_limits_change)
        self.state.current_band_changed.connect(self._on_band_change)
        self.state.save_directory_selected.connect(self._plot_model.save_all_plots)

        # View Slots
        self.view.new_image_plotted.connect(self.apply_color_map)
        self.view.current_band_changed.connect(self.update_band)
        self.view.color_limits_changed.connect(self.update_color_limits)
        self.view.activated.connect(
            lambda: self.state.set_active_image_view(self.view.view_id)
        )
        self.view.single_pixel_clicked.connect(self._click_dispatcher)
        self.view.lasso_selector.lasso_finished.connect(self.spatial_data_adapter)
        self.view.cursor_location_changed.connect(self.lasso_move)
        self.view.image_context_menu.save_all_requested.connect(
            self.state.save_requested.emit
        )

        # Canvas Connections
        self.view.canvas.mpl_connect("key_press_event", self.on_arrow_key)

        initial_band = view_state.current_band
        initial_color_limits = view_state.color_limits
        if view_state.image.has_finite_data:
            self.view.set_image_data(view_state.image)
            if 0 <= initial_band < view_state.image.nbands:
                self.view.change_image_band(initial_band)
            if initial_color_limits != (0, 0):
                self.view.update_color_limit(*initial_color_limits)
        self.view.update_color_map(view_state.color_map)

    def _on_image_change(self, view_id: object, img_data: ImageData) -> None:
        if view_id != self.view.view_id:
            return
        self.view.set_image_data(img_data)
        self._plot_model.gtrans = img_data.geotransform

    def on_arrow_key(self, event: KeyEvent):
        self.state.set_active_image_view(self.view.view_id)
        if (key := event.key) == "right":
            self.state.set_current_band(
                self.view.view_id,
                self.state.image_view_state(self.view.view_id).current_band + 1,
            )
        elif key == "left":
            self.state.set_current_band(
                self.view.view_id,
                self.state.image_view_state(self.view.view_id).current_band - 1,
            )

    def _on_color_map_change(self, view_id: object, clrmap_name: str) -> None:
        if view_id != self.view.view_id:
            return
        self.view.update_color_map(clrmap_name)

    def apply_color_map(self) -> None:
        color_map = self.state.image_view_state(self.view.view_id).color_map
        self.view.update_color_map(color_map)

    def _on_color_limits_change(
        self, view_id: object, vmin: float, vmax: float
    ) -> None:
        if view_id != self.view.view_id:
            return
        self.view.update_color_limit(vmin, vmax)

    def update_color_limits(self, vmin: float, vmax: float) -> None:
        self.state.set_color_limits(self.view.view_id, (vmin, vmax))

    def _on_band_change(self, view_id: object, band_index: int) -> None:
        if view_id == self.view.view_id:
            self.view.change_image_band(band_index)

    def update_band(self, band_index: int) -> None:
        self.state.set_active_image_view(self.view.view_id)
        self.state.set_current_band(self.view.view_id, band_index)

    def update_cursor_tracker(self, point_data: PointData) -> None:
        self.state.cursor_location = point_data

    def lasso_click(self, point_data: PointData) -> None:
        self.view.lasso_selector.start_lasso(point_data)

    def lasso_move(self, point_data: PointData) -> None:
        if self.view.pressed:
            self.view.lasso_selector.lasso_movement(point_data)

    def _click_dispatcher(self, point_data: PointData, event: MouseEvent):
        modifiers = event.modifiers
        if modifiers == frozenset({"ctrl"}):
            self.lasso_click(point_data)
        elif modifiers == frozenset({"shift"}):
            self.spatial_data_adapter(point_data)

    def spatial_data_adapter(self, input: PointData | LassoSelection) -> SpatialData:
        """Emitter of spatial data collected signal"""
        spatial_data = spatial_data_adapter(input)
        self._plot_model.create_plot(spatial_data.id)
        self._plot_model.update_plot(
            spatial_data.id, spatial_data.pixel_info, DataInputType.PIXEL
        )
        return spatial_data
