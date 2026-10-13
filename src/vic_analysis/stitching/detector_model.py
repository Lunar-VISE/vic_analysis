from dataclasses import dataclass, field
from uuid import UUID, uuid4

import numpy as np
import numpy.typing as npt

from src.vic_analysis.stitching.spatial_utilities import Bounds
from vic_analysis.detector_specs import BandName
from vic_analysis.radiance_pipeline.bias_model import BayerPattern

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
class FilterRegion(DetectorRegion):
    name: BandName
    filter_wavelength: int


@dataclass(frozen=True, kw_only=True)
class DarkRegion(DetectorRegion):
    bayer = BayerPattern()


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

    @property
    def region_names(self) -> list[str]:
        return [i.name for i in self.regions]

    def add_detector_region(self, region: DetectorRegion) -> None:
        try:
            self._validate_no_duplicates()
        except ValueError:
            raise ValueError(f"Region {region.name} already exists.")
        self.regions.append(region)

    def get_region(self, name: str) -> DetectorRegion:
        for i in self.regions:
            if i.name == name:
                return i
        raise ValueError(f"{name} is not in detector set.")


class VICDetector(DetectorSet):
    def __post_init__(self) -> None:
        super().__post_init__()
        required_regions = ["VIC_DARK", "VIC_FULL"]
        if not all(i in self.region_names for i in required_regions):
            raise ValueError(
                f"A VICDetector must contain all of the regions: {required_regions}"
            )

    @property
    def active_regions(self) -> list[FilterRegion]:
        return [i for i in self.regions if isinstance(i, FilterRegion)]

    @property
    def dark_regions(self) -> list[DarkRegion]:
        return [i for i in self.regions if isinstance(i, DarkRegion)]

    @property
    def wavelengths(self) -> list[float]:
        return [i.filter_wavelength for i in self.active_regions]

    @property
    def full_frame(self) -> DetectorRegion:
        return next(i for i in self.regions if i.name == "VIC_FULL")


VIC_FILTER1 = FilterRegion(37, 2000, 189, 0, filter_wavelength=415, name="Filter1")
VIC_FILTER2 = FilterRegion(444, 2000, 596, 0, filter_wavelength=850, name="Filter2")
VIC_FILTER3 = FilterRegion(844, 2000, 996, 0, filter_wavelength=750, name="Filter3")
VIC_FILTER4 = FilterRegion(1243, 2000, 1395, 0, filter_wavelength=565, name="Filter4")
VIC_FILTER5 = FilterRegion(1636, 2000, 1788, 0, filter_wavelength=675, name="Filter5")
VIC_FILTER6 = FilterRegion(2036, 2000, 2188, 0, filter_wavelength=900, name="Filter6")
VIC_FILTER7 = FilterRegion(2436, 2000, 2588, 0, filter_wavelength=950, name="Filter7")
VIC_DARK = DarkRegion(0, 50, VIC_DETECTOR_WIDTH, 0, name="VIC_DARK")
VIC_WHOLE_FRAME = DetectorRegion(
    0, VIC_DETECTOR_HEIGHT, VIC_DETECTOR_WIDTH, 0, name="VIC_FULL"
)

VIC_DETECTOR = DetectorSet(
    [
        VIC_FILTER1,
        VIC_FILTER2,
        VIC_FILTER3,
        VIC_FILTER4,
        VIC_FILTER5,
        VIC_FILTER6,
        VIC_FILTER7,
        VIC_DARK,
        VIC_WHOLE_FRAME,
    ]
)
