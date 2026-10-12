import numpy as np

from vic_analysis.read.cube_format import CubeFormat


def find_nan_bands(arr: np.ndarray, format: CubeFormat) -> np.ndarray:
    nan_bands = np.ones(format.nbands(arr.shape), dtype=bool)
    for band in range(nan_bands.size):
        indexer: list[int | slice] = [slice(None)] * arr.ndim
        indexer[format.band_axis] = band
        band_data = arr[tuple(indexer)]
        for row_start in range(0, band_data.shape[0], 512):
            for col_start in range(0, band_data.shape[1], 512):
                tile = band_data[
                    row_start : row_start + 512, col_start : col_start + 512
                ]
                if not np.isnan(tile).all():
                    nan_bands[band] = False
                    break
            if not nan_bands[band]:
                break
    return nan_bands
