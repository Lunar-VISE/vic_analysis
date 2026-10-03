from pathlib import Path
from typing import NamedTuple, TypeVar, overload
from uuid import UUID

import fiona
import numpy as np
from shapely import Point
from shapely.geometry import Polygon, mapping

from vic_analysis.write.spectrum_model import (
    FullSpectrumModel,
    SpectralInformation,
    SpectrumArea,
    SpectrumGroup,
)

T = TypeVar("T")


class ShapelyObject[T](NamedTuple):
    geometry: T
    id: UUID


ShapelyPolygon = ShapelyObject[Polygon]
ShapelyPoint = ShapelyObject[Point]


@overload
def shapely_points(spectral_info: FullSpectrumModel) -> ShapelyPoint: ...


@overload
def shapely_points(spectral_info: SpectrumGroup) -> list[ShapelyPoint]: ...


def shapely_points(
    spectral_info: FullSpectrumModel | SpectrumGroup,
) -> ShapelyPoint | list[ShapelyPoint]:
    if isinstance(spectral_info, FullSpectrumModel):
        if spectral_info.location.map is None:
            shapely_point = Point(*spectral_info.location.pixel.astuple())
        else:
            shapely_point = Point(*spectral_info.location.map.astuple())
        return ShapelyPoint(geometry=shapely_point, id=spectral_info.id)
    elif isinstance(spectral_info, SpectrumGroup):
        if any(i.location.map is None for i in spectral_info.spectra):
            pixel_type = "pixel"
        else:
            pixel_type = "map"
        shapely_point_list: list[ShapelyPoint] = []
        for i in spectral_info.spectra:
            pt = Point(*getattr(i.location, pixel_type).astuple())
            shapely_point_list.append(ShapelyPoint(geometry=pt, id=i.id))
        return shapely_point_list


def shapely_polygon_from_spectrum_area(spectrum_area: SpectrumArea) -> ShapelyPolygon:
    boundary_verts = spectrum_area.bounding_vertices
    if boundary_verts.geotransform is None:
        verts = np.array([i.astuple() for i in boundary_verts.pixels])
    else:
        verts = np.array([i.astuple() for i in boundary_verts.maps])

    return ShapelyPolygon(id=spectrum_area.id, geometry=Polygon(verts))


def write_shapely_polygon(
    poly: ShapelyPolygon, save_directory: Path, filename: str
) -> None:
    schema = {"geometry": "Polygon", "properties": {"id": "str"}}
    save_file = Path(save_directory, filename).with_suffix(".shp")
    with fiona.open(save_file, "w", "ESRI Shapefile", schema) as f:
        f.write({"geometry": mapping(poly.geometry), "properties": {"id": poly.id}})


def write_shapely_point(
    point: ShapelyPoint | list[ShapelyPoint], save_directory: Path, filename: str
) -> None:
    schema = {"geometry": "Point", "properties": {"id": "str"}}
    save_file = Path(save_directory, filename).with_suffix(".shp")

    with fiona.open(save_file, "w", "ESRI Shapefile", schema) as f:
        if isinstance(point, list):
            for pt in point:
                f.write({"geometry": mapping(pt.geometry), "properties": {"id": pt.id}})
        else:
            f.write(
                {"geometry": mapping(point.geometry), "properties": {"id": point.id}}
            )


def write_spectrum(
    spectral_info: SpectralInformation, save_directory: Path, save_name: str
) -> None:
    save_file = Path(save_directory, save_name)
    spectral_info.to_json(save_file.with_suffix(".json"))
    if isinstance(spectral_info, (FullSpectrumModel, SpectrumGroup)):
        write_shapely_point(
            shapely_points(spectral_info),
            save_directory=save_file.parent,
            filename=save_file.name,
        )
    else:
        write_shapely_polygon(
            shapely_polygon_from_spectrum_area(spectral_info),
            save_directory=save_file.parent,
            filename=save_file.name,
        )
