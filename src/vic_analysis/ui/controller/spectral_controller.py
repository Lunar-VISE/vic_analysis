from uuid import UUID

import numpy as np

from vic_analysis.geometry.pixels_in_polygon import find_pixels_in_polygon
from vic_analysis.numpy_dynamic_indexing import slice_along
from vic_analysis.read.cube_format import CubeFormat
from vic_analysis.ui.model.application_state import AppState
from vic_analysis.ui.model.plot_model import DataInputType, PlotModel
from vic_analysis.ui.view.spectral_view import SpectralView


class SpectralController:
    def __init__(
        self, plot_model: PlotModel, view: SpectralView, state: AppState
    ) -> None:
        self.view = view
        self.state = state
        self._plot_model = plot_model

        self._plot_model.plot_updated.connect(self._on_plot_update)
        self._plot_model.plot_renamed.connect(self.view._on_plot_rename)

    def _get_spectral_data(self, pixel_data: np.ndarray) -> np.ndarray:
        if not self.state.current_image.wavelength_is_set:
            raise ValueError("Wavelength values not set.")

        fmt = self.state.current_image.format
        temporary_reshape = fmt.convert_to(self.state.current_image.array, "RCB")

        data_to_plot = slice_along(
            temporary_reshape,
            (list(pixel_data[:, 0]), list(pixel_data[:, 1])),
            (CubeFormat.RCB.col_axis, CubeFormat.RCB.row_axis),
        )

        return data_to_plot

    def _get_mean_spectrum(self, spectral_array: np.ndarray) -> np.ndarray:
        spectrum = spectral_array.mean(axis=0)
        wvl = np.asarray(self.state.current_image.wavelength)
        return np.column_stack((wvl, spectrum))

    def _on_plot_update(self, id: UUID, data_input_type: DataInputType) -> None:
        plot = self._plot_model.get_plot_from_id(id)
        match data_input_type:
            case DataInputType.PIXEL:
                if plot.data.is_point:
                    pixel_index = plot.data.require_pixel()
                    spec_array = self._get_spectral_data(pixel_index)
                else:
                    pixel_index = find_pixels_in_polygon(plot.data.require_pixel())[
                        :, ::-1
                    ]
                    spec_array = self._get_spectral_data(pixel_index)
                    self._plot_model.update_plot(id, spec_array, DataInputType.BULK)
                spectral_data = self._get_mean_spectrum(spec_array)
                self._plot_model.update_plot(id, spectral_data, DataInputType.VECTOR)
            case _:
                return
