from dataclasses import dataclass
from typing import Self

import numpy as np

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
    _wavelength: np.ndarray | None = None
    wavelength_is_set: bool = False

    def __post_init__(self):
        if self.array.ndim != 3:
            raise ValueError("Array data must be 3-dimensional.")

    @property
    def wavelength(self) -> np.ndarray:
        if self._wavelength is None:
            raise ValueError("Wavelength values have not been set.")
        return self._wavelength

    @wavelength.setter
    def wavelength(self, val: np.ndarray) -> None:
        self._wavelength = val
        self.wavelength_is_set = True

    @classmethod
    def default(cls) -> Self:
        return cls(np.full((250, 250, 1), fill_value=np.nan), CubeFormat.RCB)
