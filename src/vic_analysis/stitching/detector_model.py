from dataclasses import dataclass, field
from uuid import UUID, uuid4

import numpy as np
import numpy.typing as npt

from src.vic_analysis.stitching.spatial_utilities import Bounds

VIC_DETECTOR_HEIGHT: int = 2004  # pixels
VIC_DETECTOR_WIDTH: int = 2752  # pixels


@dataclass(frozen=True)
class DetectorRegion:
    left: int
    bottom: int
    right: int
    top: int
    name: str = field(default="")
    id: UUID = field(default_factory=uuid4)

    @property
    def bounds(self) -> Bounds:
        return Bounds(self.left, self.bottom, self.right, self.top)

    @property
    def topleft(self) -> np.ndarray:
        return np.array([self.left, self.top])

    @property
    def bottomleft(self) -> np.ndarray:
        return np.array([self.left, self.bottom])

    @property
    def bottomright(self) -> np.ndarray:
        return np.array([self.right, self.bottom])

    @property
    def topright(self) -> np.ndarray:
        return np.array([self.right, self.top])

    @property
    def corners(self) -> npt.NDArray[np.uint]:
        return np.stack(
            [self.topleft, self.bottomleft, self.bottomright, self.topright],
            axis=0,
        )

    def __post_init__(self) -> None:
        if any(i < 0 for i in self.bounds):
            raise ValueError(f"All bounds must be non-negative: {self.bounds}")

    def check_bounds(self, height: int, width: int) -> bool:
        return not (self.bottom > height) & (self.right > width)


@dataclass(frozen=True, kw_only=True)
class VICDetectorRegion(DetectorRegion):
    filter_wavelength: int


@dataclass
class DetectorSet:
    regions: list[DetectorRegion] = field(default_factory=list)
    detector_height: int = VIC_DETECTOR_HEIGHT
    detector_width: int = VIC_DETECTOR_WIDTH

    def __post_init__(self) -> None:
        self._validate_regions_in_detector()
        self._validate_no_duplicates()

    def _validate_regions_in_detector(self) -> None:
        for region in self.regions:
            if not region.check_bounds(self.detector_height, self.detector_width):
                raise ValueError(f"Region list outside detector: {region}")

    def _validate_no_duplicates(self) -> None:
        idlist = [i.id for i in self.regions]
        if len(idlist) != len(set(idlist)):
            raise ValueError("Duplicate regions exist")

    def add_detector_region(self, region: DetectorRegion) -> None:
        try:
            self._validate_no_duplicates()
        except ValueError:
            raise ValueError(f"Region {region.name} already exists.")
        self.regions.append(region)

    def get_detector(self, name: str) -> DetectorRegion:
        for i in self.regions:
            if i.name == name:
                return i
        raise ValueError(f"{name} is not in detector set.")


VIC_FILTER1 = VICDetectorRegion(
    37, 2000, 189, 0, filter_wavelength=415, name="VIC_BAND1"
)
VIC_FILTER2 = VICDetectorRegion(
    444, 2000, 596, 0, filter_wavelength=850, name="VIC_BAND2"
)
VIC_FILTER3 = VICDetectorRegion(
    844, 2000, 996, 0, filter_wavelength=750, name="VIC_BAND3"
)
VIC_FILTER4 = VICDetectorRegion(
    1243, 2000, 1395, 0, filter_wavelength=565, name="VIC_BAND4"
)
VIC_FILTER5 = VICDetectorRegion(
    1636, 2000, 1788, 0, filter_wavelength=675, name="VIC_BAND5"
)
VIC_FILTER6 = VICDetectorRegion(
    2036, 2000, 2188, 0, filter_wavelength=900, name="VIC_BAND6"
)
VIC_FILTER7 = VICDetectorRegion(
    2436, 2000, 2588, 0, filter_wavelength=950, name="VIC_BAND7"
)

VIC_FILTERS = DetectorSet(
    [
        VIC_FILTER1,
        VIC_FILTER2,
        VIC_FILTER3,
        VIC_FILTER4,
        VIC_FILTER5,
        VIC_FILTER6,
        VIC_FILTER7,
    ]
)

VIC_WHOLE_FRAME = DetectorRegion(
    0, VIC_DETECTOR_HEIGHT, VIC_DETECTOR_WIDTH, 0, name="VIC_FULL"
)
