from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID

import numpy as np
from PySide6.QtCore import QObject, Signal

from vic_analysis.ui.model.point_data import PointData
from vic_analysis.ui.view.widgets.activity_button import ActivityButton

from .image_data import ImageData

type WavelengthValue = list[float] | Literal["NotSet"]


@dataclass
class ImageViewState:
    image: ImageData
    color_map: str = "crameri:grayc_r"
    color_limits: tuple[float, float] = (0, 0)
    current_band: int = 0


class AppState(QObject):
    image_changed = Signal(UUID, ImageData)
    colormap_changed = Signal(UUID, str)
    color_limits_changed = Signal(UUID, float, float)
    current_band_changed = Signal(UUID, int)
    home_directory_changed: Signal = Signal(Path)

    active_image_view_changed = Signal(UUID)
    cursor_location_changed = Signal(PointData)
    activity_open_requested = Signal(ActivityButton)
    activity_close_requested = Signal(ActivityButton)
    save_requested = Signal()
    save_directory_selected = Signal(Path)

    def __init__(self) -> None:
        super().__init__()
        self._home_directory = Path.cwd()
        self._image_views: dict[UUID, ImageViewState] = {}
        self._active_image_view_id: UUID | None = None
        self._cursor_location = PointData.default()
        self._wavelength: list[float] | Literal["NotSet"] = "NotSet"

    def register_image_view(self, view_id: UUID) -> ImageViewState:
        if view_id in self._image_views:
            return self._image_views[view_id]

        if self._active_image_view_id is None:
            view_state = ImageViewState(ImageData.default())
        else:
            active_state = self.image_view_state(self._active_image_view_id)
            view_state = ImageViewState(
                active_state.image,
                active_state.color_map,
                active_state.color_limits,
                active_state.current_band,
            )

        self._image_views[view_id] = view_state
        self.set_active_image_view(view_id)
        return view_state

    def image_view_state(self, view_id: UUID) -> ImageViewState:
        return self._image_views[view_id]

    @property
    def active_image_view_id(self) -> UUID:
        if self._active_image_view_id is None:
            raise RuntimeError("No image view has been registered.")
        return self._active_image_view_id

    def set_active_image_view(self, view_id: UUID) -> None:
        if view_id not in self._image_views:
            raise KeyError(f"Unknown image view: {view_id}")
        if view_id == self._active_image_view_id:
            return
        self._active_image_view_id = view_id
        self.active_image_view_changed.emit(view_id)

    def set_current_image(self, view_id: UUID, val: ImageData) -> None:
        view_state = self.image_view_state(view_id)
        if np.array_equal(view_state.image.array, val.array, equal_nan=True):
            return
        view_state.image = val
        view_state.color_limits = (0, 0)
        view_state.current_band = 0
        self.image_changed.emit(view_id, val)

    def set_color_map(self, view_id: UUID, val: str) -> None:
        view_state = self.image_view_state(view_id)
        if val == view_state.color_map:
            return
        view_state.color_map = val
        self.colormap_changed.emit(view_id, val)

    def set_color_limits(self, view_id: UUID, val: tuple[float, float]) -> None:
        view_state = self.image_view_state(view_id)
        if view_state.color_limits == val:
            return
        view_state.color_limits = val
        self.color_limits_changed.emit(view_id, val[0], val[1])

    def set_current_band(self, view_id: UUID, val: int) -> None:
        view_state = self.image_view_state(view_id)
        if view_state.current_band == val:
            return
        view_state.current_band = val
        self.current_band_changed.emit(view_id, val)

    @property
    def home_directory(self) -> Path:
        return self._home_directory

    @home_directory.setter
    def home_directory(self, val: Path) -> None:
        if val == self._home_directory:
            return
        self._home_directory = val
        self.home_directory_changed.emit(val)

    @property
    def color_map(self) -> str:
        return self.image_view_state(self.active_image_view_id).color_map

    @color_map.setter
    def color_map(self, val: str) -> None:
        self.set_color_map(self.active_image_view_id, val)

    @property
    def current_image(self) -> ImageData:
        return self.image_view_state(self.active_image_view_id).image

    @current_image.setter
    def current_image(self, val: ImageData) -> None:
        self.set_current_image(self.active_image_view_id, val)

    @property
    def color_limits(self) -> tuple[float, float]:
        return self.image_view_state(self.active_image_view_id).color_limits

    @color_limits.setter
    def color_limits(self, val: tuple[float, float]) -> None:
        self.set_color_limits(self.active_image_view_id, val)

    @property
    def current_band(self) -> int:
        return self.image_view_state(self.active_image_view_id).current_band

    @current_band.setter
    def current_band(self, val: int) -> None:
        self.set_current_band(self.active_image_view_id, val)

    @property
    def cursor_location(self) -> PointData:
        return self._cursor_location

    @cursor_location.setter
    def cursor_location(self, val: PointData) -> None:
        if self._cursor_location == val:
            return
        self._cursor_location = val
        self.cursor_location_changed.emit(val)
