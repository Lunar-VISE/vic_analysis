from pathlib import Path
from typing import Literal, TypeGuard

from vic_analysis.ui.model.image_data import ImageData

from . import loader_functions as lf

type FileSuffix = Literal[".bin", ".bsq", ".bil", ".bip", ".json"]

file_suffix_list: list[FileSuffix] = [".bin", ".bsq", ".bil", ".bip", ".json"]


def _is_valid_file_suffix(val: str) -> TypeGuard[FileSuffix]:
    return val in file_suffix_list


DATA_LOADER: dict[FileSuffix, lf.LoaderFunction] = {
    ".bin": lf.load_vic_binary,
    ".bil": lf.load_envi,
    ".bip": lf.load_envi,
    ".bsq": lf.load_envi,
    ".json": lf.load_cubio_json,
}


def load_data(filepath: lf.FilePath) -> ImageData:
    """
    Loads image data from a file.
    """
    suffix = Path(filepath).suffix
    if not _is_valid_file_suffix(suffix):
        raise ValueError(f"Invalid file suffix: {suffix}")

    return DATA_LOADER[suffix](filepath)
