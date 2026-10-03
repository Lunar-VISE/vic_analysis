from collections.abc import Generator
from dataclasses import dataclass, field
from uuid import UUID

from cmap import Color
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.markers import MarkerStyle
from matplotlib.transforms import IdentityTransform


def make_scatter(
    axes: Axes,
    size: float = 10.0,
    marker: str = "o",
    color: tuple[float, float, float, float] | str = "k",
) -> PathCollection:
    marker_style = MarkerStyle(marker)

    collection = PathCollection(
        [marker_style.get_path().transformed(marker_style.get_transform())],
        sizes=(size,),
        facecolors=(color,),
        edgecolors=(color,),
    )

    collection.set_transform(IdentityTransform())
    collection.set_offset_transform(axes.transData)
    collection.set_picker(5)

    return collection


@dataclass(frozen=True)
class PlottedArtist:
    art: Artist
    color: Color
    id: UUID

    def __eq__(self, other: object):
        if not isinstance(other, PlottedArtist):
            raise NotImplementedError

        return self.art == other.art or self.color == other.color or self.id == other.id


@dataclass
class ArtistCollection:
    _artists: list[PlottedArtist] = field(default_factory=list)

    def add_plotted_artist(self, artist: PlottedArtist) -> None:
        if any(i == artist for i in self._artists):
            raise ValueError(f"Cannot add duplicate artist: {artist}")
        self._artists.append(artist)

    def remove_plotted_artist(self, artist: PlottedArtist) -> None:
        artist.art.remove()
        self._artists.remove(artist)

    def get_id(self, id: UUID) -> PlottedArtist:
        return self._validate_query(i for i in self._artists if i.id == id)

    def get_artist(self, artist: Artist) -> PlottedArtist:
        return self._validate_query(i for i in self._artists if i.art == artist)

    def get_color(self, color: Color) -> PlottedArtist:
        return self._validate_query(i for i in self._artists if i.color == color)

    def _validate_query(self, gen: Generator[PlottedArtist]) -> PlottedArtist:
        try:
            return next(gen)
        except StopIteration:
            raise StopIteration("Artist not found")

    def check_id(self, id: UUID) -> bool:
        return any(i.id == id for i in self._artists)
