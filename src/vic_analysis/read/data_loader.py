from pathlib import Path
from typing import Literal, TypeGuard

from vic_analysis.read.image_pyramid import ImagePyramid
from vic_analysis.ui.model.image_data import ImageData

from . import loader_functions as lf

type FileSuffix = Literal[".bin", ".bsq", ".bil", ".bip", ".json", ".fits"]

file_suffix_list: list[FileSuffix] = [".bin", ".bsq", ".bil", ".bip", ".json", ".fits"]


def _is_valid_file_suffix(val: str) -> TypeGuard[FileSuffix]:
    return val in file_suffix_list


DATA_LOADER: dict[FileSuffix, lf.LoaderFunction] = {
    ".bin": lf.load_vic_binary,
    ".bil": lf.load_envi,
    ".bip": lf.load_envi,
    ".bsq": lf.load_envi,
    ".json": lf.load_cubio_json,
    ".fits": lf.load_fits,
}


def load_data(filepath: lf.FilePath) -> ImageData:
    """
    Loads image data from a file, always in RCB format.
    """
    suffix = Path(filepath).suffix
    if not _is_valid_file_suffix(suffix):
        raise ValueError(f"Invalid file suffix: {suffix}")

    loaded_data = DATA_LOADER[suffix](filepath)
    loaded_data.source_path = Path(filepath)
    if suffix != ".fits":
        loaded_data.pyramid = ImagePyramid.ensure(loaded_data.source_path, loaded_data)
        nan_bands = loaded_data.pyramid.find_nan_bands(loaded_data)
        loaded_data.nan_bands = nan_bands

    return loaded_data
