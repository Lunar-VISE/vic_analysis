from matplotlib.backend_bases import MouseEvent
from matplotlib.patches import Polygon

from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.model.lasso_selection import LassoSelection
from vic_analysis.ui.model.point_data import PointData
from vic_analysis.ui.view.image_view import ImageView
from vic_analysis.ui.view.widgets.lasso_selector import LassoState


class ImageController:
    def __init__(self, view: ImageView, state: AppState) -> None:
        self.state = state
        self.view = view

        # State Slots
        self.state.image_changed.connect(self.view.set_image_data)
        self.state.colormap_changed.connect(self.update_color_map)
        self.state.color_limits_changed.connect(self.update_color_limits)

        # View Slots
        self.view.new_image_plotted.connect(self.apply_color_map)
        self.view.current_band_changed.connect(self.update_band)
        self.view.single_pixel_clicked.connect(self.lasso_click)
        self.view.cursor_location_changed.connect(self.lasso_move)
        self.view.released.connect(self.lasso_end)

        # Lasso Slots
        self.view.lasso_selector.lasso_finished.connect(self.draw_lasso)

    def update_color_map(self, clrmap_name: str) -> None:
        self.view.update_color_map(clrmap_name)
        self.state.color_map = clrmap_name

    def apply_color_map(self) -> None:
        self.view.update_color_map(self.state.color_map)

    def update_color_limits(self, vmin: float, vmax: float) -> None:
        self.view.update_color_limit(vmin, vmax)

    def update_band(self, band_index: int) -> None:
        self.state.current_band = band_index

    def update_cursor_tracker(self, point_data: PointData) -> None:
        self.state.cursor_location = point_data

    def lasso_click(self, point_data: PointData, event: MouseEvent) -> None:
        modifiers = event.modifiers
        if modifiers == frozenset({"ctrl"}):
            self.view.lasso_selector.start_lasso(point_data)
            self._lasso_line_points = ([point_data.x], [point_data.y])
            (self._lasso_line,) = self.view.axes.plot(*self._lasso_line_points)

    def lasso_move(self, point_data: PointData) -> None:
        if self.view.pressed and (self.view.lasso_selector.state == LassoState.DRAWING):
            self.view.lasso_selector.lasso_movement(point_data)
            self._lasso_line_points[0].append(point_data.x)
            self._lasso_line_points[1].append(point_data.y)
            self._lasso_line.set_data(*self._lasso_line_points)

            self.view.canvas.draw_idle()

    def lasso_end(self) -> None:
        if self.view.lasso_selector.state == LassoState.DRAWING:
            self.view.lasso_selector.finish_lasso()

    def draw_lasso(self, lasso_selection: LassoSelection) -> None:
        print("Drawing Lasso!")
        poly = Polygon(lasso_selection.vertices)
        self.view.draw_polygon(poly)
