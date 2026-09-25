from collections.abc import Callable
from pathlib import Path

import cubio as cb
import numpy as np

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
    return ImageData(img[:, :, None], CubeFormat.RCB)


def load_envi(filepath: FilePath) -> ImageData:
    """
    Loads any ENVI-compatible dataset.
    """
    cc, cd = cb.cube_from_envi(filepath, "ENVI_DATASET")
    cd.transpose_to("BIP")
    return ImageData(
        cd.array.values,
        CubeFormat.RCB,
        np.array(cc.measurement_values),
    )


def load_cubio_json(filepath: FilePath) -> ImageData:
    """Loads a cubio-compatible json file."""
    cc, cd = cb.cube_from_json(filepath)
    cd.transpose_to("BIP")
    return ImageData(
        cd.array.values,
        CubeFormat.RCB,
        np.array(cc.measurement_values),
    )
