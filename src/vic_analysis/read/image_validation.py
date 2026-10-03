import numpy as np

from vic_analysis.read.cube_format import CubeFormat


def find_nan_bands(arr: np.ndarray, format: CubeFormat) -> np.ndarray:
    nan_bands = np.all(np.isnan(arr), axis=(format.row_axis, format.col_axis))
    return nan_bands
