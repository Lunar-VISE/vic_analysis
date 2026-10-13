from dataclasses import dataclass
from pathlib import Path
from typing import Self

from astropy.io import fits
from astropy.io.fits import ImageHDU

from vic_analysis.read.data_loader import load_data
from vic_analysis.ui.model.image_data import ImageData


@dataclass
class VICHeader:
    band_id: int
    image_id: int
    azimuth_position: int
    nrows: int
    ncols: int
    integration_time: int

    @classmethod
    def from_fits_header(cls, header: fits.Header) -> Self:
        return cls(
            band_id=header["BAND_ID"],
            image_id=header["IMG_ID"],
            azimuth_position=header["AZ_POS"],
            nrows=header["NUM_ROWS"],
            ncols=header["NUM_COLS"],
            integration_time=header["VNIR_INT"],
        )

    @property
    def shape(self) -> tuple[int, int]:
        return (self.nrows, self.ncols)


class L0FileContents:
    def __init__(self) -> None:
        self.image_list: list[ImageHDU] = []
        self.header_list: list[VICHeader] = []
        self._current_index = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> tuple[ImageHDU, VICHeader]:
        if self._current_index < len(self.image_list):
            return_val = (
                self.image_list[self._current_index],
                self.header_list[self._current_index],
            )
            self._current_index += 1
            return return_val
        raise StopIteration

    @property
    def img_ids(self) -> list[int]:
        return [i.image_id for i in self.header_list]

    @property
    def band_ids(self) -> list[int]:
        return [i.band_id for i in self.header_list]

    @property
    def azimuth_positions(self) -> list[int]:
        return [i.azimuth_position for i in self.header_list]

    @property
    def integration_times(self) -> list[int]:
        return [i.integration_time for i in self.header_list]


class VICL0File:
    def __init__(self, filepath: Path | str) -> None:
        self.fp = filepath
        self.contents: L0FileContents = L0FileContents()
        self.file: fits.HDUList | None = None

    def __enter__(self) -> L0FileContents:
        self.file: fits.HDUList = fits.open(self.fp)
        for _n, i in enumerate(self.file):
            if isinstance(i, ImageHDU):
                self.contents.image_list.append(i)
                self.contents.header_list.append(VICHeader.from_fits_header(i.header))
        return self.contents

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.file is not None:
            self.file.close()


@dataclass
class L0FileData:
    image: ImageData
    metadata: list[VICHeader]

    def __post_init__(self) -> None:
        nimgs = self.image.array.shape[self.image.format.band_axis]
        if nimgs != len(self.metadata):
            raise ValueError(
                f"Number of images {nimgs} does not match metadata list {len(self.metadata)}"
            )


def read_l0_pipeline_file(filepath: Path | str) -> L0FileData:
    imgdat = load_data(filepath)
    # with VICL0File(filepath) as f:
    #     metadata = f.header_list

    # return L0FileData(imgdat, metadata)
