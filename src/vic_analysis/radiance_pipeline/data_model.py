from dataclasses import dataclass, field
from enum import IntFlag, auto
from typing import Self
from uuid import UUID, uuid4

import numpy as np

from vic_analysis.detector_specs import DETECTOR_SIZE
from vic_analysis.numpy_dynamic_indexing import get_flat_indices, slice_along
from vic_analysis.read.lv_pipeline import VICHeader

# from vic_analysis.numpy_dynamic_indexing import Indexer

type SliceIndex = slice[int, int]


class VICProcessingFlags(IntFlag):
    NO_PROCESSING = 0
    SATURATION_FLAGS_MADE = auto()
    BIAS_REMOVED = auto()
    GAIN_APPLIED = auto()


@dataclass
class DataValues:
    shape: tuple[int, int]
    values: np.ndarray
    indices: np.ndarray

    def make_array(self) -> np.ndarray:
        frame = np.full(self.shape, fill_value=np.nan)
        frame[self.indices] = self.values
        return frame


@dataclass
class VICDataset:
    data: DataValues
    masked_region: DataValues
    header: VICHeader
    uuid: UUID = field(default_factory=uuid4)
    processing_flags: VICProcessingFlags = field(
        default=VICProcessingFlags.NO_PROCESSING
    )

    @classmethod
    def build(
        cls,
        image_slice: np.ndarray,
        header: VICHeader,
        active_region: tuple[SliceIndex, SliceIndex] = (
            slice(50, DETECTOR_SIZE[0]),
            slice(0, 152),
        ),
        dark_region: tuple[SliceIndex, SliceIndex] = (slice(0, 50), slice(0, 152)),
    ) -> Self:
        shape = header.shape
        active_values = slice_along(image_slice, active_region, (0, 1))
        dark_values = slice_along(image_slice, dark_region, (0, 1))
        active_flat_indices = get_flat_indices(active_region, shape)
        dark_flat_indices = get_flat_indices(dark_region, shape)
        return cls(
            DataValues(shape=shape, values=active_values, indices=active_flat_indices),
            DataValues(shape=shape, values=dark_values, indices=dark_flat_indices),
            header,
        )


class VICPanorama:
    def __init__(self) -> None:
        self.datasets: list[VICDataset]
        self._regular_grid: np.ndarray | None = None
