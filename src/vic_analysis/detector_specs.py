from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from pydantic import BaseModel, field_validator

type BandName = Literal[
    "Filter1", "Filter2", "Filter3", "Filter4", "Filter5", "Filter6", "Filter7"
]
band_names: list[BandName] = [
    "Filter1",
    "Filter2",
    "Filter3",
    "Filter4",
    "Filter5",
    "Filter6",
    "Filter7",
]

type OtherRegion = Literal["Dark", "Whole"]

# Size of the entire VIC detector
DETECTOR_SIZE: tuple[int, int] = (2004, 2752)

# Conversion from shutter width (IT) to exposure time (s)
IT_CONVERSION = 1.214e-4

# Number of dark rows at the top of a VIC image
NUM_DARK_ROWS = 50


class DetectorRegionBounds(BaseModel):
    left: int
    bottom: int
    right: int
    top: int

    @field_validator("left", "bottom", "right", "top")
    @classmethod
    def validate_non_negative(cls, v):
        if v < 0:
            raise ValueError("Coordinates must be non-negative")
        return v

    @field_validator("right")
    @classmethod
    def validate_right_greater_left(cls, v, info):
        if "left" in info.data and v <= info.data["left"]:
            raise ValueError(
                f"right ({v}) must be greater than left ({info.data['left']})"
            )
        return v

    @field_validator("bottom")
    @classmethod
    def validate_bottom_greater_top(cls, v, info):
        if "top" in info.data and v <= info.data["top"]:
            raise ValueError(
                f"bottom ({v}) must be greater than top ({info.data['top']})"
            )
        return v

    def idx(self) -> tuple[slice, slice]:
        return slice(self.top, self.bottom), slice(self.left, self.right)

    def get_size(self) -> int:
        return (self.right - self.left) * (self.bottom - self.top)

    def get_shape(self) -> tuple[int, int]:
        return (self.bottom - self.top), (self.right - self.left)


class DetectorRegionInfo(BaseModel):
    region_id: BandName | OtherRegion
    band_center_wavelength: int
    band_width: int


class DetectorRegion(BaseModel):
    info: DetectorRegionInfo
    bounds: DetectorRegionBounds

    @classmethod
    def build(
        cls,
        region_id: BandName | OtherRegion,
        band_center_wavelength: int,
        band_width: int,
        left_bound: int,
        bottom_bound: int,
        right_bound: int,
        top_bound: int,
    ) -> "DetectorRegion":
        return cls(
            info=DetectorRegionInfo(
                region_id=region_id,
                band_center_wavelength=band_center_wavelength,
                band_width=band_width,
            ),
            bounds=DetectorRegionBounds(
                left=left_bound,
                bottom=bottom_bound,
                right=right_bound,
                top=top_bound,
            ),
        )

    def idx(self) -> tuple[slice, slice]:
        return self.bounds.idx()

    def get_center_region(self, buffer=10) -> "DetectorRegion":
        idx = self.idx()
        center_y = (idx[0].stop + idx[0].start) // 2
        center_x = (idx[1].stop + idx[1].start) // 2
        return DetectorRegion.build(
            region_id=self.info.region_id,
            band_center_wavelength=self.info.band_center_wavelength,
            band_width=self.info.band_width,
            left_bound=center_x - buffer,
            bottom_bound=center_y + buffer,
            right_bound=center_x + buffer,
            top_bound=center_y - buffer,
        )

    @property
    def center(self) -> tuple[float, float]:
        idx = self.idx()
        center_y = (idx[0].stop + idx[0].start) // 2
        center_x = (idx[1].stop + idx[1].start) // 2
        return center_x, center_y

    @property
    def size(self):
        return self.bounds.get_size()

    @property
    def shape(self):
        return self.bounds.get_shape()


class Detector(BaseModel):
    name: str
    region_set: dict[BandName | OtherRegion, DetectorRegion]

    def get_wavelengths(self) -> np.ndarray:
        return np.array(
            [
                i.info.band_center_wavelength
                for i in self.region_set.values()
                if i.info.band_center_wavelength != 0
            ]
        )


DARK_REGION: DetectorRegion = DetectorRegion.build("Dark", 0, 0, 0, 32, 2752, 0)

WHOLE_VIC: DetectorRegion = DetectorRegion.build("Whole", 0, 0, 0, 2004, 2752, 0)

VIC_FILTER_REGIONS: Detector = Detector(
    name="VIC",
    region_set={
        "Filter1": DetectorRegion.build("Filter1", 415, 30, 11, 1990, 224, 60),
        "Filter2": DetectorRegion.build("Filter2", 850, 40, 428, 1990, 618, 60),
        "Filter3": DetectorRegion.build("Filter3", 750, 40, 828, 1990, 1013, 60),
        "Filter4": DetectorRegion.build("Filter4", 565, 40, 1223, 1990, 1408, 60),
        "Filter5": DetectorRegion.build("Filter5", 675, 40, 1619, 1990, 1805, 60),
        "Filter6": DetectorRegion.build("Filter6", 900, 40, 2021, 1990, 2206, 60),
        "Filter7": DetectorRegion.build("Filter7", 950, 40, 2413, 1990, 2617, 60),
        "Dark": DARK_REGION,
    },
)

EDU_FILTER_REGIONS: Detector = Detector(
    name="EDU",
    region_set={
        "Filter2": DetectorRegion.build("Filter2", 850, 40, 212, 1850, 364, 115),
        "Filter3": DetectorRegion.build("Filter3", 750, 40, 612, 1850, 765, 115),
        "Filter4": DetectorRegion.build("Filter4", 565, 40, 1014, 1850, 1155, 115),
        "Filter5": DetectorRegion.build("Filter5", 675, 40, 1416, 1850, 1548, 115),
        "Filter6": DetectorRegion.build("Filter6", 900, 40, 1812, 1850, 1938, 115),
        "Filter7": DetectorRegion.build("Filter7", 950, 40, 2208, 1850, 2391, 115),
        "Dark": DARK_REGION,
    },
)


VIC_FLAT_FIELD_REGIONS: Detector = Detector(
    name="VIC_FF",
    region_set={
        "Filter1": DetectorRegion.build("Filter1", 415, 30, 75, 980, 175, 680),
        "Filter2": DetectorRegion.build("Filter2", 850, 40, 470, 1220, 570, 920),
        "Filter3": DetectorRegion.build("Filter3", 750, 40, 890, 690, 990, 390),
        "Filter4": DetectorRegion.build("Filter4", 565, 40, 1270, 1120, 1370, 820),
        "Filter5": DetectorRegion.build("Filter5", 675, 40, 1670, 1190, 1770, 890),
        "Filter6": DetectorRegion.build("Filter6", 900, 40, 2065, 920, 2165, 620),
        "Filter7": DetectorRegion.build("Filter7", 950, 40, 2460, 1160, 2560, 860),
    },
)

EDU_FLAT_FIELD_REGIONS: Detector = Detector(
    name="EDU_FF",
    region_set={
        "Filter2": DetectorRegion.build("Filter2", 850, 40, 246, 1182, 326, 1050),
        "Filter3": DetectorRegion.build("Filter3", 750, 40, 665, 564, 745, 437),
        "Filter4": DetectorRegion.build("Filter4", 565, 40, 1068, 1749, 1148, 1610),
        "Filter5": DetectorRegion.build("Filter5", 675, 40, 1446, 693, 1526, 531),
        "Filter6": DetectorRegion.build("Filter6", 900, 40, 1827, 1089, 1907, 942),
        "Filter7": DetectorRegion.build("Filter7", 950, 40, 2250, 1221, 2320, 1035),
    },
)


def full_detector_to_region_dict(
    full_detector_array: np.ndarray, detector: Detector = VIC_FILTER_REGIONS
) -> dict[BandName | OtherRegion, np.ndarray]:
    """
    Convert a full detector array to a dictionary of region arrays.

    Parameters
    ----------
    full_detector_array: 2D numpy array
        Full detector array to convert to region arrays.
    detector: Detector
        Detector object containing the region definitions.

    Returns
    -------
    dict[BandName | OtherRegion, np.ndarray]
        Dictionary of region arrays keyed by region name.
    """
    region_dict: dict[BandName | OtherRegion, np.ndarray] = {}
    for k, v in detector.region_set.items():
        region_dict[k] = full_detector_array[*v.idx(), ...]
    return region_dict


def show_filter_diagram(
    detector_name: Literal["VIC", "EDU"],
    include_flat_field_regions: bool = False,
):
    if detector_name == "VIC":
        detector: Detector = VIC_FILTER_REGIONS
        ff_regions: Detector = VIC_FLAT_FIELD_REGIONS
    elif detector_name == "EDU":
        detector = EDU_FILTER_REGIONS
        ff_regions = EDU_FLAT_FIELD_REGIONS
    _f, ax = plt.subplots(figsize=(14, 8))

    ax.add_patch(Rectangle((0, 0), *DETECTOR_SIZE[::-1], color="gray"))

    for k, v in detector.region_set.items():
        clr = "cornflowerblue"
        if k == "Dark":
            clr = "k"
        rect = Rectangle(
            (v.bounds.left, v.bounds.top),
            *v.shape[::-1],
            facecolor=clr,
            edgecolor="k",
            linewidth=1,
        )
        ax.add_patch(rect)
        if k == "Dark":
            continue
            ax.text(*v.center, k, rotation=0, size=24)
        else:
            ax.text(
                v.center[0] - 10,
                v.center[1],
                f"{k} ({v.info.band_center_wavelength} nm)",
                rotation=90,
                size=24,
            )

    if include_flat_field_regions:
        for k, v in ff_regions.region_set.items():
            rect = Rectangle(
                (v.bounds.left, v.bounds.top),
                *v.shape[::-1],
                color="moccasin",
            )
            ax.add_patch(rect)
    ax.set_ylim(DETECTOR_SIZE[0], 0)
    ax.set_xlim(0, DETECTOR_SIZE[1])
    ax.set_aspect("equal")
    plt.show()
    ax.set_aspect("equal")
    plt.show()
