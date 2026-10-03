from collections.abc import Callable
from pathlib import Path

import cubio as cb
import numpy as np
from astropy.io import fits

from vic_analysis.geometry.geotransform import convert_cubio_geotransform
from vic_analysis.ui.model.image_data import ImageData

from .cube_format import CubeFormat
from .parse_vic_binary import parse_file_name

type FilePath = str | Path
type LoaderFunction = Callable[[FilePath], ImageData]


def load_vic_binary(filepath: FilePath) -> ImageData:
    """
    Loads a VIC .bin file, as in the files taken in the Paul's Rocks
    collection.
    """
    info = parse_file_name(filepath)
    nrows, ncols = info.image_size
    img = np.memmap(info.filepath, dtype=">u2", shape=(nrows, ncols))
    imgdata = ImageData(img[:, :, None], CubeFormat.RCB)

    return imgdata


def load_envi(filepath: FilePath) -> ImageData:
    """
    Loads any ENVI-compatible dataset.
    """
    cc, cd = cb.cube_from_envi(filepath, "ENVI_DATASET")
    cd.transpose_to("BIP")
    imgdata = ImageData(
        cd.array.values,
        CubeFormat.RCB,
        geotransform=convert_cubio_geotransform(cc.geotransform),
    )

    imgdata.wavelength = cc.measurement_values

    return imgdata


def load_cubio_json(filepath: FilePath) -> ImageData:
    """Loads a cubio-compatible json file."""
    cc, cd = cb.cube_from_json(filepath)
    cd.transpose_to("BIP")
    imgdata = ImageData(
        cd.array.values,
        CubeFormat.RCB,
        geotransform=convert_cubio_geotransform(cc.geotransform),
    )

    imgdata.wavelength = cc.measurement_values

    return imgdata


def load_fits(filepath: FilePath) -> ImageData:
    """
    Loads a .fits with a possible ImageHDU named 'WVL' containing wavelength
    values.
    """
    with fits.open(filepath) as hdul:
        names = [hdu.name for hdu in hdul]
        if "PRIMARY" in names:
            cube: np.ndarray = hdul["PRIMARY"].data
        else:
            raise ValueError("Primary Cube HDU does not exist.")

        wvl: np.ndarray | None = None
        if "WVL" in names:
            wvl: np.ndarray = hdul["WVL"].data
        else:
            wvl = None

    imgdata = ImageData(cube, CubeFormat.BRC)
    if wvl is not None:
        imgdata.wavelength = [float(i) for i in wvl]

    return imgdata
