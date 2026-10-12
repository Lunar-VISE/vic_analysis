from collections.abc import Iterator
from dataclasses import dataclass, field, fields
from math import sqrt
from typing import Self

import numpy as np


@dataclass
class BayerSlice:
    """Bayer Pattern Slice obejct."""

    r1: tuple[slice, slice] = (slice(0, None, 2), slice(0, None, 4))
    r2: tuple[slice, slice] = (slice(0, None, 2), slice(2, None, 4))
    g11: tuple[slice, slice] = (slice(0, None, 2), slice(1, None, 4))
    g12: tuple[slice, slice] = (slice(1, None, 2), slice(0, None, 4))
    g21: tuple[slice, slice] = (slice(0, None, 2), slice(3, None, 4))
    g22: tuple[slice, slice] = (slice(1, None, 2), slice(2, None, 4))
    b1: tuple[slice, slice] = (slice(1, None, 2), slice(1, None, 4))
    b2: tuple[slice, slice] = (slice(1, None, 2), slice(3, None, 4))


@dataclass
class BayerPattern:
    """
    Bayer pattern bias values for each color channel.

    +------+------+------+------+
    |  R1  | G11  |  R2  | G21  |
    +------+------+------+------+
    | G12  |  B1  | G22  |  B2  |
    +------+------+------+------+
    """

    r1: float = 0.0
    r2: float = 0.0
    g11: float = 0.0
    g12: float = 0.0
    g21: float = 0.0
    g22: float = 0.0
    b1: float = 0.0
    b2: float = 0.0

    @classmethod
    def iter_from_array(cls, values: np.ndarray) -> Iterator[Self]:
        """Yield one Bayer pattern for each complete 2x4 cell in ``values``."""
        if values.ndim != 2:
            raise ValueError("Bayer pixel array must be two-dimensional")

        height, width = values.shape
        if height == 0 or width == 0 or height % 2 != 0 or width % 4 != 0:
            raise ValueError(
                "Bayer pixel array dimensions must be positive multiples of 2x4"
            )

        bayer_slice = BayerSlice()
        component_arrays = {
            item.name: values[getattr(bayer_slice, item.name)] for item in fields(cls)
        }
        cell_indices = np.ndindex(height // 2, width // 4)
        return (
            cls(
                **{
                    name: float(component_array[index])
                    for name, component_array in component_arrays.items()
                }
            )
            for index in cell_indices
        )

    def full_detector(self, detector_size: tuple[int, int]) -> np.ndarray:
        """Expand the bayer pattern bias to a full array of a given size."""
        bias = np.empty(detector_size)
        byr = BayerSlice()
        bias[*byr.r1] = self.r1
        bias[*byr.r2] = self.r2
        bias[*byr.g11] = self.g11
        bias[*byr.g12] = self.g12
        bias[*byr.g21] = self.g21
        bias[*byr.g22] = self.g22
        bias[*byr.b1] = self.b1
        bias[*byr.b2] = self.b2
        return bias

    def __sub__(self, other: Self) -> Self:
        if isinstance(other, self.__class__):
            return self.__class__(
                self.r1 - other.r1,
                self.r2 - other.r2,
                self.g11 - other.g11,
                self.g12 - other.g12,
                self.g21 - other.g21,
                self.g22 - other.g22,
                self.b1 - other.b1,
                self.b2 - other.b2,
            )
        else:
            raise NotImplementedError("Unsupported operand type for __sub__")

    def __add__(self, other: Self) -> Self:
        return self.__class__(
            self.r1 + other.r1,
            self.r2 + other.r2,
            self.g11 + other.g11,
            self.g12 + other.g12,
            self.g21 + other.g21,
            self.g22 + other.g22,
            self.b1 + other.b1,
            self.b2 + other.b2,
        )

    def __truediv__(self, other: Self | float) -> Self:
        if isinstance(other, self.__class__):
            return self.__class__(
                self.r1 / other.r1,
                self.r2 / other.r2,
                self.g11 / other.g11,
                self.g12 / other.g12,
                self.g21 / other.g21,
                self.g22 / other.g22,
                self.b1 / other.b1,
                self.b2 / other.b2,
            )
        elif isinstance(other, (int, float)):
            return self.__class__(
                self.r1 / other,
                self.r2 / other,
                self.g11 / other,
                self.g12 / other,
                self.g21 / other,
                self.g22 / other,
                self.b1 / other,
                self.b2 / other,
            )
        else:
            raise NotImplementedError("Unsupported operand type for __truediv__")

    def __floordiv__(self, other: Self | float) -> Self:
        return self.__truediv__(other)

    def __mul__(self, other: Self) -> Self:
        return self.__class__(
            self.r1 * other.r1,
            self.r2 * other.r2,
            self.g11 * other.g11,
            self.g12 * other.g12,
            self.g21 * other.g21,
            self.g22 * other.g22,
            self.b1 * other.b1,
            self.b2 * other.b2,
        )


@dataclass
class VICBias:
    """Stores bayer pattern bias data."""

    _mean: BayerPattern = field(default_factory=BayerPattern)
    _moment: BayerPattern = field(default_factory=BayerPattern)
    _count: int = 0

    def add_dark_region(self, masked_pixels: np.ndarray) -> None:
        """
        Adds the dark region pixels to the running mean and moment calculations.

        Parameters
        ----------
        masked_pixels : np.ndarray
            An array of dark region pixels to be added to the running mean and
            variance calculations.
        """
        for cell in BayerPattern.iter_from_array(masked_pixels):
            self._count += 1
            old_mean = self._mean
            delta = cell - self._mean
            self._mean += delta / self._count
            self._moment += (cell - old_mean) * (cell - self._mean)

    def get_mean(self) -> BayerPattern:
        """
        Returns the mean for each color channel.
        """
        return self._mean

    def get_sample_variance(self) -> BayerPattern:
        """
        Returns the sample variance for each color channel.
        """
        return self._moment / (self._count - 1)

    def get_sample_stdev(self) -> BayerPattern:
        """
        Returns the sample standard deviation for each color channel.
        """
        var = self.get_sample_variance()
        return BayerPattern(
            r1=sqrt(var.r1),
            r2=sqrt(var.r2),
            g11=sqrt(var.g11),
            g12=sqrt(var.g12),
            g21=sqrt(var.g21),
            g22=sqrt(var.g22),
            b1=sqrt(var.b1),
            b2=sqrt(var.b2),
        )

    def get_sdom(self) -> BayerPattern:
        """
        Returns the standard deviation of the mean (sdom) for each color
        channel.The sdom is calculated as the sample standard deviation divided
        by the square root of the number of samples.
        """
        return self.get_sample_stdev() / sqrt(self._count)
