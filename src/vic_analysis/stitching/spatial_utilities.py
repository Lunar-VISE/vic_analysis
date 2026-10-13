from dataclasses import dataclass
from typing import NamedTuple, Self

import numpy as np
import numpy.typing as npt
from matplotlib.patches import Polygon


def get_flat_indices(index: tuple[slice, slice], shape: tuple[int, int]) -> np.ndarray:
    return np.ravel_multi_index(np.ogrid[*index], shape).ravel()


@dataclass
class GeometricImage:
    values: npt.NDArray[np.float32]
    indices: npt.NDArray[np.int32]
    height: int
    width: int
    pixel_coords: npt.NDArray[np.uint]

    def __len__(self) -> int:
        return self.values.size

    def __post_init__(self) -> None:
        self._validate_array_dimensions()
        self._validate_array_sizes()

    def _validate_array_dimensions(self) -> None:
        if self.values.ndim != 1:
            raise ValueError("Pixel values should be a 1D array in C-order.")
        if self.indices.ndim != 1:
            raise ValueError("Indices should be a 1D array of integers.")
        if self.pixel_coords.ndim != 2:
            raise ValueError("Pixel coordinates should be a 2D array.")

    def _validate_array_sizes(self) -> None:
        if self.values.size != self.indices.size:
            raise ValueError("Values and indices must be the same size.")
        if self.values.size != self.pixel_coords.shape[0]:
            raise ValueError(
                "The number of rows in pixel coordinates must be the same as"
                "the size of pixel values."
            )

    def to_image(self) -> npt.NDArray[np.float32]:
        img_array = np.full(self.width * self.height, fill_value=np.nan)
        img_array[self.indices] = self.values
        return img_array.reshape(self.height, self.width)

    @classmethod
    def from_image(
        cls, image: npt.NDArray, topmost_pixel: int, leftmost_pixel: int
    ) -> Self:
        if image.ndim != 2:
            raise ValueError(f"Invalid Image Size: {image.shape}")

        rows, columns = np.indices(image.shape)
        pixel_coords = np.column_stack([columns.ravel(), rows.ravel()])
        pixel_coords[:, 0] += leftmost_pixel
        pixel_coords[:, 1] += topmost_pixel

        indices = np.arange(image.size, dtype=np.int32)

        return cls(
            values=image.ravel(),
            indices=indices,
            height=image.shape[0],
            width=image.shape[1],
            pixel_coords=pixel_coords,
        )


class Bounds(NamedTuple):
    left: int
    bottom: int
    right: int
    top: int

    @property
    def center(self) -> tuple[float, float]:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)


class ExtentPolygon(Polygon):
    def __init__(self, xy: np.ndarray, **kwargs) -> None:
        super().__init__(xy, **kwargs)
        self._validate_xy(xy)
        self.topleft = xy[0, :]
        self.bottomleft = xy[1, :]
        self.bottomright = xy[2, :]
        self.topright = xy[3, :]

    @property
    def bounds(self) -> Bounds:
        left = max(self.topleft[0], self.bottomleft[0])
        right = max(self.topright[0], self.bottomright[0])
        top = max(self.topleft[1], self.topright[1])
        bottom = max(self.bottomleft[1], self.bottomright[1])
        return Bounds(left, bottom, right, top)

    @property
    def center(self) -> tuple[float, float]:
        return self.bounds.center

    @staticmethod
    def _validate_xy(xy: np.ndarray) -> None:
        if xy.shape != (4, 2):
            raise ValueError("Extent must contain exactly four 2D points.")
        if not np.isfinite(xy).all():
            raise ValueError("Extent points must be finite.")

        top_left, bottom_left, bottom_right, top_right = xy
        if not (
            (top_left[0] + bottom_left[0]) < (top_right[0] + bottom_right[0])
            and (top_left[1] + top_right[1]) > (bottom_left[1] + bottom_right[1])
        ):
            raise ValueError(
                "Points must be ordered top left, bottom left, bottom right, top right."
            )

        edges = np.roll(xy, -1, axis=0) - xy
        cross_products = edges[:, 0] * np.roll(edges[:, 1], -1) - edges[:, 1] * np.roll(
            edges[:, 0], -1
        )
        if np.any(cross_products == 0) or not (
            np.all(cross_products > 0) or np.all(cross_products < 0)
        ):
            raise ValueError("Extent points must form a non-degenerate convex polygon.")
