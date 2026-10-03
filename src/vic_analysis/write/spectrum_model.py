from pathlib import Path
from typing import Literal, Self
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel

from vic_analysis.geometry.geotransform import GeotransformModel
from vic_analysis.geometry.pixel_model import PixelGroupModel, PixelModel
from vic_analysis.geometry.pixels_in_polygon import find_pixels_in_polygon

type WavelengthUnits = Literal["m", "um", "nm"]
type SpectralInformation = FullSpectrumModel | SpectrumArea | SpectrumGroup


class WavelengthModel(BaseModel):
    values: list[float]
    bad_bands: list[float]
    unit: WavelengthUnits


class BaseSpectrumModel(BaseModel):
    values: list[float]
    location: PixelModel
    id: UUID


class FullSpectrumModel(BaseSpectrumModel):
    wavelength: WavelengthModel

    def to_json(self, savefile: Path) -> None:
        with open(savefile, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def build(
        cls,
        spectral_array: np.ndarray,
        pixel: np.ndarray,
        id: UUID,
        bad_bands: list[bool] | None = None,
        wavelength_units: WavelengthUnits = "um",
        geotransform: GeotransformModel | None = None,
    ) -> Self:
        if bad_bands is None:
            bad_bands = [False for _ in range(spectral_array.shape[0])]
        wvl = WavelengthModel(
            values=spectral_array[:, 0], bad_bands=bad_bands, unit=wavelength_units
        )
        loc = PixelModel.build(x=pixel[0, 0], y=pixel[0, 1], geotransform=geotransform)
        return cls(values=spectral_array[:, 1], location=loc, id=id, wavelength=wvl)


class SpectrumArea(BaseModel):
    wavelength: WavelengthModel
    mean_spectrum: list[float]
    spectra_population: list[BaseSpectrumModel]
    bounding_vertices: PixelGroupModel
    id: UUID

    def to_json(self, savefile: Path) -> None:
        with open(savefile, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def build(
        cls,
        spectral_array: np.ndarray,
        bulk_array: np.ndarray,
        pixel: np.ndarray,
        id: UUID,
        bad_bands: list[bool] | None = None,
        wavelength_units: WavelengthUnits = "um",
        geotransform: GeotransformModel | None = None,
    ) -> Self:
        if bad_bands is None:
            bad_bands = [False for _ in range(spectral_array.shape[0])]
        wvl = WavelengthModel(
            values=spectral_array[:, 0], bad_bands=bad_bands, unit=wavelength_units
        )
        verts = PixelGroupModel.build(pixel, geotransform)
        population: list[BaseSpectrumModel] = []
        pixel_index = find_pixels_in_polygon(pixel)
        for n in range(bulk_array.shape[0]):
            vals = bulk_array[n, :]
            loc = PixelModel.build(
                x=pixel_index[n, 0], y=pixel_index[n, 1], geotransform=geotransform
            )
            population.append(BaseSpectrumModel(values=vals, location=loc, id=uuid4()))
        return cls(
            mean_spectrum=spectral_array[:, 1],
            spectra_population=population,
            id=id,
            wavelength=wvl,
            bounding_vertices=verts,
        )


class SpectrumGroup(BaseModel):
    wavelength: WavelengthModel
    spectra: list[BaseSpectrumModel]

    def to_json(self, savefile: Path) -> None:
        with open(savefile, "w") as f:
            f.write(self.model_dump_json(indent=2))
