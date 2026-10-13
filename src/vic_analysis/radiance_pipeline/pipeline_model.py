from collections.abc import Sequence

from tqdm import tqdm

from vic_analysis.detector_specs import NUM_DARK_ROWS
from vic_analysis.radiance_pipeline.data_model import VICDataset
from vic_analysis.radiance_pipeline.step_model import Step
from vic_analysis.read.lv_pipeline import L0FileContents, VICL0File


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
