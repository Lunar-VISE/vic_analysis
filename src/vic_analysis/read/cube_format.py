"""
Utility Enum for standardizing hyperspectral cube arrays.
"""

from enum import StrEnum
from typing import Literal, Self, cast

import numpy as np

type CubeFormatLiteral = Literal[
    "RBC",
    "BCR",
    "BRC",
    "RCB",
    "CBR",
    "CRB",
    "BSQ",
    "BIL",
    "BIP",
]

type CubeFilename = Literal["BSQ", "BIL", "BIP"]


class CubeFormat(StrEnum):
    """
    Used to standardize 3D hyperspectral cube arrays. Uses the initials:
    ```
    B = Band
    C = Column
    R = Row
    ```
    to map out which array axis corresponds to which part of the hyperspectral
    cube. Also, the standard array storage formats (.bip, .bil and .bsq) are
    included as aliases for their respective formats.

    Examples
    --------
    BCR: axis 0 = Band, axis 1 = Column, axis 2 = Row (.BSQ format)

    RBC: axis 0 = Row, axis 1 = Band, axis 2 = Column (.BIL format)
    """

    RBC = "RBC"
    """
    Row, Band, Column format. Used in the Band Interleaved by Line (.bil)
    binary storage format.
    """
    RCB = "RCB"
    """
    Row, Column, Band format. Used in the Band Interleaved by Pixel (.bip)
    binary storage format.
    """
    BRC = "BRC"
    """
    Band, Row, Column format. Used in the Band Sequential (.bsq) binary storage
    format.
    """
    BCR = "BCR"
    """
    Band, Column, Row format. Not typically used for cube storage.
    """
    CRB = "CRB"
    """
    Column, Row, Band format. Not typically used for cube storage.
    """
    CBR = "CBR"
    """
    Column, Band, Row format. Not typically used for cube storage.
    """
    BSQ = "BRC"
    """
    Band Sequential format. Alias for BCR.
    """
    BIP = "RCB"
    """
    Band Interleaved by Pixel format. Alias for RCB.
    """
    BIL = "RBC"
    """
    Band Interleaved by Line format. Alias for RBC.
    """

    @property
    def standard_idx(self) -> tuple[int, int, int]:
        """
        The index tuple that will transform the current format into a
        standard RCB format.
        """
        return {
            CubeFormat.RBC: (0, 2, 1),
            CubeFormat.BCR: (2, 1, 0),
            CubeFormat.BRC: (1, 2, 0),
            CubeFormat.RCB: (0, 1, 2),
            CubeFormat.CBR: (2, 0, 1),
            CubeFormat.CRB: (1, 0, 2),
        }[self]

    @property
    def row_axis(self) -> int:
        return self.index("R")

    @property
    def col_axis(self) -> int:
        return self.index("C")

    @property
    def band_axis(self) -> int:
        return self.index("B")

    def standardize(self, data: np.ndarray) -> np.ndarray:
        """
        Take the cube that is in the current format and return a cube in the
        standard BIP format.
        """
        return np.transpose(data, self.standard_idx)

    def transpose_to_idx(
        self, target: Self | CubeFormatLiteral
    ) -> tuple[int, int, int]:
        """
        Returns the index that will transform the current format to a target
        format.
        """
        target = self.__class__[target]
        transpose_list = tuple([self.index(axis) for axis in target])
        return cast(tuple[int, int, int], transpose_list)

    def convert_to(
        self, data: np.ndarray, target: Self | CubeFormatLiteral
    ) -> np.ndarray:
        """
        Converts data from the current format to a target format.

        Parameters
        ----------
        data: np.ndarary
            Data to convert
        target: CubeFormat | CubeFormatLiteral
            Format to convert the data to

        Returns
        -------
        np.ndarray
            Converted data as numpy array.
        """
        return np.transpose(data, self.transpose_to_idx(target))

    def get_file_suffix(self) -> CubeFilename:
        """
        Returns the file name associated with the cube format.
        """
        if self in ["RBC", "BIL"]:
            return "BIL"
        if self in ["RCB", "BIP"]:
            return "BIP"
        if self in ["BRC", "BSQ"]:
            return "BSQ"
        else:
            raise ValueError(f"Invalid format for a save file: {self}")

    def nrows(self, shape: tuple[int, int, int]):
        """Gets the number of rows given a cube shape tuple."""
        return shape[self.index("R")]

    def ncols(self, shape: tuple[int, int, int]):
        """Gets the number of columns given a cube shape tuple."""
        return shape[self.index("C")]

    def nbands(self, shape: tuple[int, int, int]):
        """Gets the number of bands given a cube shape tuple."""
        return shape[self.index("B")]
