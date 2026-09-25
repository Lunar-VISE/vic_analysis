import numpy as np

from vic_analysis.numpy_dynamic_indexing import slice_along
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.model.image_data import ImageData
from vic_analysis.ui.view.hisotgram_view import HistogramView


def no_nan(arr: np.ndarray) -> np.ndarray:
    return arr[np.isfinite(arr)]


class HistogramController:
    def __init__(self, view: HistogramView, state: AppState) -> None:
        self.view = view
        self.state = state

        self.state.image_changed.connect(self.image_updated)
        self.state.current_band_changed.connect(self.band_updated)
        self.view.color_limits_change_requested.connect(self.update_color_limits)

    def band_updated(self, band_index: int) -> None:
        """
        Plots new histogram when a new band index is available.
        """
        clean = no_nan(
            slice_along(
                self.state.current_image.array,
                band_index,
                self.state.current_image.format.band_axis,
            )
        )
        self.view.draw_new_histogram(clean)

    def image_updated(self, image_data: ImageData) -> None:
        """
        Plots new histogram when a new image_data is available.
        """
        clean = no_nan(
            slice_along(
                image_data.array,
                self.state.current_band,
                image_data.format.band_axis,
            )
        )
        self.view.draw_new_histogram(clean)

    def update_color_limits(self, vmin: float, vmax: float):
        self.view.update_histogram(clims := (vmin, vmax))
        self.state.color_limits = clims
