from dataclasses import dataclass, field
from typing import Self
from uuid import UUID, uuid4

from alphashape import alphashape
from shapely.geometry import Polygon


@dataclass(frozen=True)
class PointData:
    x: float
    y: float
    xpixel: int
    ypixel: int
    id: UUID = field(default_factory=uuid4)

    @property
    def point(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def pixel(self) -> tuple[float, float]:
        return (self.ypixel, self.xpixel)

    @classmethod
    def default(cls) -> Self:
        return cls(0, 0, 0, 0)


@dataclass
class PointCollection:
    points: list[PointData]

    @property
    def pixel_list(self) -> list[tuple[float, float]]:
        return [(pt.pixel[1], pt.pixel[0]) for pt in self.points]

    def get_enclosing_polygon(self) -> Polygon:
        return alphashape(self.pixel_list, alpha=0.9)  # type: ignore
