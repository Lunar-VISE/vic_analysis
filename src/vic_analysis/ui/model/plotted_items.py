from dataclasses import dataclass, field
from uuid import UUID, uuid4

from matplotlib.collections import PathCollection
from matplotlib.patches import Polygon


@dataclass(frozen=True)
class PlottedPolygon:
    mpl_poly: Polygon
    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class PlottedScatterPoint:
    mpl_scatter: PathCollection
    id: UUID = field(default_factory=uuid4)


@dataclass
class PlottedItems:
    polygons: list[PlottedPolygon] = field(default_factory=list)
    scatter_points: list[PlottedScatterPoint] = field(default_factory=list)
