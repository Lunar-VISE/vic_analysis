from collections.abc import Callable
from pathlib import Path

import cubio as cb
import numpy as np
from astropy.io import fits
from astropy.io.fits import HDUList, ImageHDU

from vic_analysis.detector_specs import FILTER_SIZE
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
        cd.array.data,
        CubeFormat.RCB,
        geotransform=convert_cubio_geotransform(cc.geotransform),
    )
    imgdata.source_dependencies = (Path(filepath).with_suffix(".hdr"),)

    imgdata.wavelength = cc.measurement_values

    return imgdata


def load_cubio_json(filepath: FilePath) -> ImageData:
    """Loads a cubio-compatible json file."""
    cc, cd = cb.cube_from_json(filepath)
    cd.transpose_to("BIP")
    imgdata = ImageData(
        cd.array.data,
        CubeFormat.RCB,
        geotransform=convert_cubio_geotransform(cc.geotransform),
    )
    data_directory = Path(cc.retrieval_path).parent
    data_stem = Path(cc.data_filename).stem
    data_suffixes = {".img", ".bil", ".bip", ".bsq", ".tif", ".tiff", ".zarr"}
    imgdata.source_dependencies = tuple(
        sorted(
            path
            for path in data_directory.glob(f"{data_stem}.*")
            if path.suffix.lower() in data_suffixes
        )
    )

    imgdata.wavelength = cc.measurement_values

    return imgdata


def _validate_LV_pipeline_file(file: HDUList) -> bool:
    if file[0].data is not None:
        raise ValueError("Primary HDU must be empty in LV Pipeline Fits file.")

    if not all(isinstance(i, ImageHDU) for i in file[1:]):
        raise ValueError("All other HDUs must be ImageHDUs.")

    if not all(i.shape == FILTER_SIZE for i in file[1:]):
        raise ValueError(f"All ImageHDUs must be of size {FILTER_SIZE}")

    return True


def load_LV_pipeline_fits(filepath: FilePath) -> ImageData:
    with fits.open(filepath) as hdul:
        if not isinstance(hdul, HDUList):
            raise TypeError(f"Invalid HDUList: {hdul}")
        _validate_LV_pipeline_file(hdul)

        cube = np.empty((*FILTER_SIZE, len(hdul) - 1), dtype=np.float32)
        for n, hdu in enumerate(hdul[1:]):
            print(
                f"Loading image: {n + 1} of {len(hdul) - 1} ({(n + 1) / (len(hdul) - 1):.2%})",
                end="\r",
            )
            cube[:, :, n] = hdu.data
        print("\n")

        imgdata = ImageData(cube, CubeFormat.RCB)
        imgdata.wavelength = [i for i in range(len(hdul))]
        return imgdata


def load_fits(filepath: FilePath) -> ImageData:
    """
    Loads a .fits with a possible ImageHDU named 'WVL' containing wavelength
    values.
    """
    with fits.open(filepath, memmap=True) as hdul:
        # === Truncate if the fits file is in the LV Pipeline Format ===
        if _validate_LV_pipeline_file(hdul):
            return load_LV_pipeline_fits(filepath)

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
