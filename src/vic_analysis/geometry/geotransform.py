# Built-ins
from typing import Literal

import numpy as np
from affine import Affine
from cubio.geotools.models.geotransform_model import GeotransformModel as CubioGeotrans

# Dependencies
from pydantic import BaseModel
from typing_extensions import Self

from .bounding_box import BoundingBoxModel
from .point_model import PointModel, convert_cubio_point


class GeographicBoundsError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class GeotransformModel(BaseModel):
    """
    Object representing an affine geotransform matrix.

    Parameters
    ----------
    upperleft: PointModel
        Map coordinates of the upper left point of the raster.
    xres: float
        east-west resolution of the raster in map_unit/pixel.
    row_rotation: float
        Amount of rotation for the rows. Usually 0.
    yres: float
        north-south resolution of the raster in map_unit/pixel.
    col_rotation
        Amount of rotation for the columns. Usually 0.
    """

    upperleft: PointModel
    xres: float
    row_rotation: float
    yres: float
    col_rotation: float

    @classmethod
    def null(cls, northup: bool = True):
        n = -1 if northup else 1
        return cls(
            upperleft=PointModel(x=0, y=0),
            xres=1,
            row_rotation=0,
            yres=n * 1,
            col_rotation=0,
        )

    @classmethod
    def fromgdal(
        cls, gdal_transform: tuple[float, float, float, float, float, float]
    ) -> Self:
        """Creates a GeotransformModel from a GDAL-style geotransform."""
        upper_left_pt = PointModel(x=gdal_transform[0], y=gdal_transform[3])
        return cls(
            upperleft=upper_left_pt,
            xres=gdal_transform[1],
            row_rotation=gdal_transform[2],
            yres=gdal_transform[5],
            col_rotation=gdal_transform[4],
        )

    @classmethod
    def fromaffine(cls, affine_transform: Affine) -> Self:
        upper_left_pt = PointModel(x=affine_transform.c, y=affine_transform.f)
        return cls(
            upperleft=upper_left_pt,
            xres=affine_transform.a,
            row_rotation=affine_transform.b,
            yres=affine_transform.e,
            col_rotation=affine_transform.d,
        )

    @classmethod
    def fromarraysize(
        cls,
        upper_left_latitiude: float,
        upper_left_longitude: float,
        lower_right_latitude: float,
        lower_right_longitude: float,
        height: int,
        width: int,
    ) -> Self:
        upper_left_pt = PointModel(x=upper_left_longitude, y=upper_left_latitiude)
        lower_right_pt = PointModel(x=lower_right_longitude, y=lower_right_latitude)
        xres = abs(upper_left_pt.x - lower_right_pt.x) / width
        yres = abs(upper_left_pt.y - lower_right_pt.y) / height
        return cls(
            upperleft=upper_left_pt,
            xres=xres,
            row_rotation=0,
            yres=-yres,
            col_rotation=0,
        )

    def togdal(self) -> tuple[float, float, float, float, float, float]:
        """Returns a GDAL-style geotransform."""
        return (
            self.upperleft.x,
            self.xres,
            self.row_rotation,
            self.upperleft.y,
            self.col_rotation,
            self.yres,
        )

    def toaffine(self) -> Affine:
        return Affine(
            a=self.xres,
            b=self.row_rotation,
            c=self.upperleft.x,
            d=self.col_rotation,
            e=self.yres,
            f=self.upperleft.y,
        )

    def get_bbox(self, height: int, width: int):
        """Given the height and width of a raster, return a bounding box."""
        return BoundingBoxModel(
            left=self.upperleft.x,
            bottom=self.upperleft.y + (height * self.yres),
            right=self.upperleft.x + (width * self.xres),
            top=self.upperleft.y,
            name="bbox",
        )

    def pixel_to_map(
        self,
        xpixel: float,
        ypixel: float,
        convention: Literal["globe", "hemi"] = "hemi",
    ) -> PointModel:
        """Convert a pixel coordinate point to a map coordinate point."""
        xmap = self.upperleft.x + xpixel * self.xres + ypixel * self.row_rotation
        ymap = self.upperleft.y + ypixel * self.yres + xpixel * self.col_rotation

        if (convention == "globe") and (xmap < 0):
            xmap += 360
        return PointModel(x=xmap, y=ymap)

    def map_to_pixel(self, xmap: float, ymap: float) -> PointModel:
        """Convert a map coordinate point to a pixel coordinate point."""
        _scaler = (self.xres * self.yres) - (self.col_rotation * self.row_rotation)
        xpixel = (
            (self.yres * xmap)
            - (self.upperleft.x * self.yres)
            - ((self.row_rotation * self.yres) / self.xres) * ymap
            + (self.row_rotation * self.upperleft.y)
        ) / _scaler
        ypixel = (
            (self.xres * ymap)
            - (self.upperleft.y * self.xres)
            - ((self.col_rotation * self.xres) / self.yres) * xmap
            + (self.col_rotation * self.upperleft.x)
        ) / _scaler

        if xpixel < 0:
            raise GeographicBoundsError(
                f"{xmap} is beyond the left X bound: {self.upperleft.x}"
            )
        if ypixel < 0:
            raise GeographicBoundsError(
                f"{ymap} is beyond the top bound: {self.upperleft.y}"
            )
        return PointModel(x=xpixel, y=ypixel)

    def generate_coords(
        self, *, width: int, height: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Generates coordinate using the given geotransform for an array of size
        xsize by ysize.

        Parameters
        ----------
        xsize : int
            Size of the desired coordinate grid in the x direction (width).
        ysize : int
            Size of the desired coordinate grid in the y direction (height).

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            Tuple of (x-coordinates, y-coordinates).
        """
        xcoords = np.empty(width, dtype=np.float32)
        ycoords = np.empty(height, dtype=np.float32)
        for nx in range(width):
            xcoords[nx] = self.pixel_to_map(xpixel=nx, ypixel=0).x
        for ny in range(height):
            ycoords[ny] = self.pixel_to_map(xpixel=0, ypixel=ny).y
        return xcoords, ycoords

    def force_northup(self):
        self.yres = -abs(self.yres)


def convert_cubio_geotransform(gtrans: CubioGeotrans) -> GeotransformModel:
    """
    Interfaces between this Geotransform Model and the cubio one.
    """
    return GeotransformModel(
        upperleft=convert_cubio_point(gtrans.upperleft),
        xres=gtrans.xres,
        row_rotation=gtrans.row_rotation,
        yres=gtrans.yres,
        col_rotation=gtrans.col_rotation,
    )
