from enum import StrEnum, auto


class ButtonName(StrEnum):
    FOLDER = auto()
    HISTOGRAM = auto()
    DEFAULT = auto()


TOOLTIP_DICT: dict[ButtonName, str] = {
    ButtonName.FOLDER: "Directory Tree",
    ButtonName.HISTOGRAM: "Histogram Viewer",
}
