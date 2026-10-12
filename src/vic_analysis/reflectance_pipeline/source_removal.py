from pathlib import Path
from typing import Literal

import cubio as cb
import numpy as np
from cubio.data.crs_wkt_strings import GeographicCRS
from cubio.geotools.models.geotransform_model import GeotransformModel

from vic_analysis.read.cube_format import CubeFormat
from vic_analysis.read.data_loader import load_data
from vic_analysis.reflectance_pipeline.source_retrieval import (
    get_halogen_source,
    load_saved_spectrum_directory,
    scale_spectra_to_unity_reflectance,
)

type SourceType = Literal["halogen_bulb", "solar"]


def _validate_cube_size(cube: np.ndarray, format: CubeFormat, spec: np.ndarray):
    if cube.shape[format.band_axis] != spec.size:
        raise ValueError(
            f"Cube {cube.shape} and Spectrum {spec.shape} to not match in size"
        )


def remove_source_spectrum(
    radiance_cube: np.ndarray, format: CubeFormat, source_spectrum: np.ndarray
) -> np.ndarray:
    """
    Removes an arbitrary source spectrum from a radiance cube to get
    reflectance.
    """
    _validate_cube_size(radiance_cube, format, source_spectrum)
    rdn_cube_rcb = format.convert_to(radiance_cube, CubeFormat.RCB)
    print(source_spectrum)
    return rdn_cube_rcb / source_spectrum[None, None, :]


def save_cube(
    cube: np.ndarray, wvl: np.ndarray | list[float], name: str, directory: str | Path
) -> None:
    cc, cd = cb.cube_from_numpy(
        cube,
        "BIP",
        name=name,
        crs=GeographicCRS.WGS84,
        gtrans=GeotransformModel.null(),
        measvals=list(wvl),
    )
    cb.write_envi(cc, cd, "BIL", directory)


def execute_source_removal(
    radiance_cube_fp: Path | str,
    source: np.ndarray | SourceType,
    savedir: str | Path,
    savename: str,
    spectralon_directory: Path | str | None = None,
) -> np.ndarray:
    imgdata = load_data(radiance_cube_fp)
    cube_arr = imgdata.array
    if isinstance(source, np.ndarray):
        source_array = source
    elif isinstance(source, str):
        if source == "halogen_bulb":
            if spectralon_directory is None:
                raise ValueError(
                    "If source == `halogen_bulb`, then spectralon spectra must be provided"
                )
            spectralon_spectra = load_saved_spectrum_directory(spectralon_directory)
            scale_spectra_to_unity_reflectance(spectralon_spectra)
            source_array = get_halogen_source(spectralon_spectra)
        elif source == "solar":
            raise NotImplementedError("Solar Spectrum Removal has not been implemented")

    reflectance_cube = remove_source_spectrum(cube_arr, CubeFormat.RCB, source_array)
    save_cube(reflectance_cube, imgdata.wavelength, savename, savedir)

    return reflectance_cube


if __name__ == "__main__":
    # load_saved_spectrum_directory("D:/panorama_testing")
    execute_source_removal(
        "D:/panorama_testing/vic_pano3_100726_55degrees/vic_pano3_RDN.json",
        source="halogen_bulb",
        spectralon_directory="D:/panorama_testing/vic_pano3_100726_55degrees/spectralon_targets/",
        savedir="D:/panorama_testing/vic_pano3_100726_55degrees/",
        savename="vic_pano3_RFL",
    )
