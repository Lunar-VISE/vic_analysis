from importlib.resources import files

import numpy as np

from vic_analysis.detector_specs import band_names
from vic_analysis.reflectance_pipeline.spectrum_resampler import (
    SpectralResponseFunction,
)
from vic_analysis.resources.dss_spreadsheet_parser import (
    get_band_response,
    get_data_from_xl,
)


def get_vic_band_responses(
    wvl_min: float, wvl_max: float
) -> list[SpectralResponseFunction]:
    excel_data = get_data_from_xl(
        str(
            files("vic_analysis").joinpath(
                "resources/DSS_Spectra_As-run_consolidated_2025cal.xlsx"
            )
        )
    )
    response_list: list[SpectralResponseFunction] = []
    for band in band_names:
        wvl, response = get_band_response(excel_data, band)
        spec = SpectralResponseFunction(response, wvl)
        spec.crop_to_wavelengths(wvl_min, wvl_max)
        response_list.append(spec)

    response_list.sort(key=lambda x: np.average(x.wvl, weights=x.rsp))

    return response_list
