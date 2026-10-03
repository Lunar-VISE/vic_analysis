from typing import Self

from cubio.geotools.models import PointModel as CubioPoint
from pydantic import BaseModel


class PointModel(BaseModel):
    """Representation of a ordered pair"""

    x: float
    y: float

    def astuple(self):
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, xy_tuple: tuple[float, float]) -> Self:
        return cls(x=xy_tuple[0], y=xy_tuple[1])


def convert_cubio_point(pt: CubioPoint) -> PointModel:
    return PointModel(x=pt.x, y=pt.y)
