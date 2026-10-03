from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

import numpy as np
from cubio.geotools.models import GeotransformModel

from .lasso_selection import LassoSelection
from .point_data import PointData

type ReferenceFrame = Literal["Image", "Geographic"]


def _validate_pixel_array(pixel_array: np.ndarray) -> None:
    if pixel_array.ndim != 2:
        raise ValueError(
            f"Pixel array has the wrong number of dimensions: {pixel_array.ndim}"
        )
    if pixel_array.shape[1] != 2:
        raise ValueError(
            f"Invalid Pixel Array size: {pixel_array.shape}. Should be (N, 2)."
        )


@dataclass
class SpatialData:
    pixel_info: np.ndarray
    id: UUID
    geotransform: GeotransformModel = field(default_factory=GeotransformModel.null)
    reference_frame: ReferenceFrame = "Image"

    def __post_init__(self) -> None:
        _validate_pixel_array(self.pixel_info)

    def transform_to_geographic(self):
        """Transforms pixels into the set geotransform coordinates."""
        for n in self.pixel_info.shape[0]:
            map_coords = self.geotransform.pixel_to_map(
                self.pixel_info[n, 0], self.pixel_info[n, 1]
            )
            self.pixel_info[n, :] = (map_coords.x, map_coords.y)

    @property
    def x_pixel_list(self) -> list[int]:
        return [i for i in self.pixel_info[:, 0]]

    @property
    def y_pixel_list(self) -> list[int]:
        return [i for i in self.pixel_info[:, 1]]


def spatial_data_adapter(input: PointData | LassoSelection) -> SpatialData:
    if isinstance(input, PointData):
        point_array = np.array(input.pixel)[None, :]
        return SpatialData(pixel_info=point_array[:, ::-1], id=input.id)
    elif isinstance(input, LassoSelection):
        return SpatialData(pixel_info=input.vertices, id=input.id)
