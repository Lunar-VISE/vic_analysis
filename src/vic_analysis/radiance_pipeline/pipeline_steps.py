from pathlib import Path
from typing import Literal
from warnings import warn

import numpy as np
from astropy.io import fits

from vic_analysis.detector_specs import IT_CONVERSION
from vic_analysis.radiance_pipeline.bias_model import VICBias
from vic_analysis.radiance_pipeline.data_model import VICDataset, VICProcessingFlags
from vic_analysis.radiance_pipeline.step_model import Step


class MakeSaturationFlags(Step):
    def __init__(
        self,
        name: str = "bias_removed",
        enabled: bool = True,
        save: bool = True,
    ) -> None:
        super().__init__(name, enabled, save)

    def run(self, dset: VICDataset) -> VICDataset:
        saturated_flags = np.zeros_like(dset.data.values)
        saturated_flags[dset.data.values == 4095]
        dset.processing_flags |= VICProcessingFlags.SATURATION_FLAGS_MADE
        return dset


class RemoveBias(Step):
    def __init__(
        self,
        dark_data: list[np.ndarray] | Literal["auto"] = "auto",
        name: str = "bias_removed",
        enabled: bool = True,
        save: bool = True,
    ) -> None:
        self._darks = dark_data
        self.bias = VICBias()
        super().__init__(name, enabled, save)

    def run(self, dset: VICDataset) -> VICDataset:
        if self._darks == "auto":
            self._darks = [dset.masked_region.values]
        for i in self._darks:
            self.bias.add_dark_region(i)
        dset.data.values -= self.bias.get_mean().full_detector(dset.data.shape)
        return dset


class ApplyGain(Step):
    """
    Applies instrument gain to get radiance values from DN.

    Parameters
    ----------
    gain_map_filepath: Path | str
        File path to gain map as a .fits file.
    integration_time: int
        Integration time in integer IT units. Conversion to seconds will be performed.
    """

    def __init__(
        self,
        gain_map_filepath: Path | str,
        name: str = "gain_applied",
        enabled: bool = True,
        save: bool = True,
    ) -> None:
        super().__init__(name, enabled, save)
        with fits.open(gain_map_filepath) as f:
            self.gain: np.ndarray = f[0].data
        self._int_time: int | None = None

    @property
    def integration_time(self) -> float:
        if self._int_time is None:
            raise AttributeError("Integration time has not been set.")
        return self._int_time

    @integration_time.setter
    def integration_time(self, val: int) -> None:
        if self.integration_time == val:
            warn("Integration time was not changed during reset.")
            return
        self._int_time = val

    def run(self, dset: VICDataset) -> VICDataset:
        dset.data.values /= self.gain
        dset.data.values = dset.data.values / (self.integration_time * IT_CONVERSION)
        return dset
