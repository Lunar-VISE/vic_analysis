from collections.abc import Sequence
from pathlib import Path
from typing import Self

from astropy.io import fits
from astropy.io.fits.hdu.image import ImageHDU
from tqdm import tqdm

from vic_analysis.detector_specs import NUM_DARK_ROWS
from vic_analysis.radiance_pipeline.data_model import VICDataset, VICHeader
from vic_analysis.radiance_pipeline.step_model import Step


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


class VICRadiancePipeline:
    def __init__(self, l0fits: L0FileContents, steps: Sequence[Step]) -> None:
        self.steps = steps
        self.l0fits = l0fits
        self._num_files = len(l0fits.image_list)
        print(f"{self._num_files} Science Images Loaded...")

    def perform_radiance_calibration(self, dset: VICDataset) -> VICDataset:
        for step in self.steps:
            dset = step.execute(dset)
        return dset

    def run(self) -> None:
        pbar = tqdm(self.l0fits, total=self._num_files)
        for image, header in pbar:
            active_region = (slice(NUM_DARK_ROWS, header.nrows), slice(0, header.ncols))
            dark_region = (slice(0, NUM_DARK_ROWS), slice(0, header.ncols))
            dset = VICDataset.build(
                image.data,
                header,
                active_region,
                dark_region,
            )
            dset = self.perform_radiance_calibration(dset)


if __name__ == "__main__":
    import vic_analysis.radiance_pipeline.pipeline_steps as ps

    steps: list[Step] = [
        ps.RemoveBias(enabled=False),
        ps.ApplyGain("D:/VIC_gain_maps/gain_map_v2.fits", enabled=False),
    ]

    fp = "D:/panorama_testing/vic_pano2_100626_90degrees/lvise_vic_l0_20261006t191403_v000.fits"

    with VICL0File(
        "D:/panorama_testing/vic_pano2_100626_90degrees/lvise_vic_l0_20261006t191403_v000.fits"
    ) as vic:
        pipeline = VICRadiancePipeline(vic, steps)
        pipeline.run()
