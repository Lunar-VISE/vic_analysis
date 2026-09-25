import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Literal, TypeGuard

type CameraType = Literal["VNIR", "IR"]
camera_types: list[CameraType] = ["VNIR", "IR"]

type FileData = dict[BandName, list[FileInfo]]

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


def is_valid_band_name(val: str) -> TypeGuard[BandName]:
    return val in band_names


def _is_camera_type(value: str) -> TypeGuard[CameraType]:
    return value in camera_types


@dataclass
class FileInfo:
    """
    Stores metadata info that can be found in panorama file names.
    """

    camera: CameraType
    date: datetime
    integration: float
    measurement_id: int
    image_size: tuple[int, int]
    filepath: Path

    ID_TO_BAND: ClassVar[dict[int, BandName]] = {
        4: "Filter1",
        5: "Filter2",
        6: "Filter3",
        7: "Filter4",
        8: "Filter5",
        9: "Filter6",
        10: "Filter7",
    }

    @property
    def vic_band(self) -> BandName:
        return self.ID_TO_BAND[self.measurement_id]


def parse_file_name(file_path: str | Path) -> FileInfo:
    """
    Parses a file path into a FileInfo object.

    Parameters
    ----------
    file_path: str | Path
        Full file path to data.

    Returns
    -------
    FileInfo
        Information about the file from the file name.
    """
    pattern = (
        r"(?P<camera>VNIR|IR)_"
        r"(?P<date_and_time>\d{8}_\d{6}_\d+)_"
        r"IT(?P<integration_time>\d+)_"
        r"(?P<measurement_id>\d+)_"
        r"(?P<columns>\d+)x"
        r"(?P<rows>\d+)"
    )
    file_path = Path(file_path)
    file_name = file_path.stem
    match = re.match(pattern, file_name)
    if match is None:
        raise ValueError(f"Invalid file name: {file_name}")

    date_string = "%Y%m%d_%H%M%S_%f"

    cam = match["camera"]
    if not _is_camera_type(cam):
        raise ValueError("Invalid Camera Type")

    dt = datetime.strptime(match["date_and_time"], date_string).replace(tzinfo=UTC)

    return FileInfo(
        cam,
        dt,
        float(match["integration_time"]),
        measurement_id=int(match["measurement_id"]),
        image_size=(int(match["rows"]), int(match["columns"])),
        filepath=file_path,
    )
