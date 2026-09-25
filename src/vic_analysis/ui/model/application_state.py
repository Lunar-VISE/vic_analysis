from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, Signal

from vic_analysis.ui.model.point_data import PointData

from .image_data import ImageData


class AppState(QObject):
    image_changed: Signal = Signal(ImageData)
    home_directory_changed: Signal = Signal(Path)
    colormap_changed: Signal = Signal(str)
    color_limits_changed: Signal = Signal(float, float)
    current_band_changed: Signal = Signal(int)
    cursor_location_changed: Signal = Signal(PointData)

    def __init__(self) -> None:
        super().__init__()
        self._color_map = ""
        self._current_image = ImageData.default()
        self._color_limits = (0, 0)
        self._current_band = 0
        self._cursor_location = PointData.default()

    @property
    def color_map(self) -> str:
        return self._color_map

    @color_map.setter
    def color_map(self, val: str) -> None:
        if val == self._color_map:
            return
        self._color_map = val
        self.colormap_changed.emit(val)

    @property
    def current_image(self) -> ImageData:
        return self._current_image

    @current_image.setter
    def current_image(self, val: ImageData) -> None:
        if np.array_equal(self._current_image.array, val.array):
            return
        self._current_image = val
        self.image_changed.emit(val)

    @property
    def color_limits(self) -> tuple[float, float]:
        return self._color_limits

    @color_limits.setter
    def color_limits(self, val: tuple[float, float]) -> None:
        if self._color_limits == val:
            return
        self._color_limits = val
        self.color_limits_changed.emit(val[0], val[1])

    @property
    def current_band(self) -> int:
        return self._current_band

    @current_band.setter
    def current_band(self, val: int) -> None:
        if self._current_band == val:
            return
        self._current_band = val
        self.current_band_changed.emit(val)

    @property
    def cursor_location(self) -> PointData:
        return self._cursor_location

    @cursor_location.setter
    def cursor_location(self, val: PointData) -> None:
        if self._cursor_location == val:
            return
        self._cursor_location = val
        self.cursor_location_changed.emit(val)
