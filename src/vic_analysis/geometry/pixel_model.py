from typing import Self

import numpy as np
from pydantic import BaseModel, computed_field

from vic_analysis.geometry.geotransform import GeotransformModel
from vic_analysis.geometry.point_model import PointModel


class PixelModel(BaseModel):
    pixel: PointModel
    geotransform: GeotransformModel | None = None

    @computed_field
    @property
    def map(self) -> PointModel | None:
        if self.geotransform is None:
            return None
        return self.geotransform.pixel_to_map(*self.pixel.astuple())

    @classmethod
    def build(
        cls, x: float, y: float, geotransform: GeotransformModel | None = None
    ) -> Self:
        return cls(pixel=PointModel(x=x, y=y), geotransform=geotransform)


class PixelGroupModel(BaseModel):
    pixels: list[PointModel]
    geotransform: GeotransformModel | None = None

    @computed_field
    @property
    def maps(self) -> list[PointModel]:
        if self.geotransform is None:
            return [PointModel(x=np.nan, y=np.nan) for _ in self.pixels]
        return [self.geotransform.pixel_to_map(*i.astuple()) for i in self.pixels]

    @classmethod
    def build(
        cls, pixel_array: np.ndarray, geotransform: GeotransformModel | None = None
    ) -> Self:
        pixel_list: list[PointModel] = []
        for n in range(pixel_array.shape[0]):
            pixel_list.append(PointModel(x=pixel_array[n, 0], y=pixel_array[n, 1]))
        return cls(pixels=pixel_list, geotransform=geotransform)
