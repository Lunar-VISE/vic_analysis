from dataclasses import KW_ONLY, dataclass
from typing import Self

import numpy as np

from vic_analysis.geometry.geotransform import GeotransformModel
from vic_analysis.read.cube_format import CubeFormat


@dataclass
class ImageData:
    """
    Stores hyperspectral image cube data.

    Attributes
    ----------
    array: np.ndarray
        Numpy array of cube data. It is always ndim=3. If the data is only a
        2D image, the third dimension will be a squeezable size of 1.
    format: CubeFormat
        Format of the data cube. See `read.cube_format`.
    wavelength: np.ndarray
        Wavelength values. If the image is 2D or does not have wavelength
        values associated with it, calling this attribute will raise a
        ValueError.

    Raises
    ------
    ValueError
        If `wavelength` is called on a dataset that does not have wavelength
        values or if the wavelength values were erroneously not set.
    """

    array: np.ndarray
    format: CubeFormat
    _: KW_ONLY
    geotransform: GeotransformModel | None = None
    _nan_bands: np.ndarray | None = None
    _wavelength: list[float] | None = None
    wavelength_is_set: bool = False

    def __post_init__(self):
        if self.array.ndim != 3:
            raise ValueError("Array data must be 3-dimensional.")

    @property
    def nbands(self) -> int:
        return self.array.shape[self.format.band_axis]

    @property
    def wavelength(self) -> list[float]:
        if self._wavelength is None:
            raise ValueError("Wavelength values have not been set.")
        return self._wavelength

    @wavelength.setter
    def wavelength(self, val: list[float]) -> None:
        self._wavelength = val
        self.wavelength_is_set = True

    @property
    def nan_bands(self) -> np.ndarray:
        if self._nan_bands is None:
            return np.zeros(self.nbands, dtype=bool)
        return self._nan_bands

    @nan_bands.setter
    def nan_bands(self, val: np.ndarray) -> None:
        if val.dtype != bool:
            raise ValueError("Cannot set nan_bands with a non-boolean array.")

        if val.ndim > 1:
            raise ValueError("nan_bands must be 1 dimensional.")

        if val.size != self.nbands:
            raise ValueError(
                f"nan_bands (length={val.size}) must be equal in length to"
                f"number of bands in the array: {self.nbands}"
            )

        self._nan_bands = val

    def get_first_valid_band(self) -> int:
        idx = int(np.argmax(self.nan_bands == False))
        return idx

    @classmethod
    def default(cls) -> Self:
        return cls(np.full((250, 250, 1), fill_value=np.nan), CubeFormat.RCB)
