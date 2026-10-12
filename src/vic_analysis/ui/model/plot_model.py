import itertools
from collections import deque
from collections.abc import Generator
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from uuid import UUID

import numpy as np
from cmap import Color
from PySide6.QtCore import QObject, Signal

from vic_analysis.geometry.geotransform import GeotransformModel
from vic_analysis.ui.model.color_manager import ColorManager
from vic_analysis.write.shapely_interface import write_spectrum
from vic_analysis.write.spectrum_model import FullSpectrumModel, SpectrumArea


class NameQueue:
    def __init__(self):
        self._values: Generator[str] = (f"Plot{i}" for i in itertools.count(1, 1))
        self._pending: deque[str] = deque()

    def next(self) -> str:
        if self._pending:
            val = self._pending.popleft()
            return val
        return next(self._values)

    def add_to(self, val: str) -> None:
        self._pending.append(val)


class DataInputType(StrEnum):
    PIXEL = auto()
    VECTOR = auto()
    SCALAR = auto()
    BULK = auto()


@dataclass
class PlotData:
    pixel: np.ndarray | None = None
    vector: np.ndarray | None = None
    scalar: np.ndarray | None = None
    bulk: np.ndarray | None = None

    def require_pixel(self) -> np.ndarray:
        if self.pixel is None:
            raise ValueError("PlotData does not have a Pixel Value")
        return self.pixel

    def require_vector(self) -> np.ndarray:
        if self.vector is None:
            raise ValueError("PlotData does not have a Vector Value")
        return self.vector

    def require_scalar(self) -> np.ndarray:
        if self.scalar is None:
            raise ValueError("PlotData does not have a Scalar Value")
        return self.scalar

    def require_bulk(self) -> np.ndarray:
        if self.bulk is None:
            raise ValueError("PlotData does not have a Bulk Value")
        return self.bulk

    @property
    def is_point(self) -> bool:
        if self.pixel is not None:
            return self.pixel.shape[0] == 1
        return False


@dataclass
class Plot:
    id: UUID
    name: str
    color: Color
    visibility: bool
    data: PlotData = field(default_factory=PlotData)
    _original_name: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._original_name = self.name

    @property
    def original_name(self) -> str:
        return self._original_name


class PlotModel(QObject):
    plot_created = Signal(UUID)
    plot_removed = Signal(UUID)
    plot_updated = Signal(UUID, DataInputType)
    plot_renamed = Signal(UUID, str)
    plot_hovered = Signal(UUID, bool)

    def __init__(
        self,
        geotransform: GeotransformModel | None = None,
        colormap_name: str = "seaborn:tab20",
        ncolors: int = 20,
    ) -> None:
        self.gtrans = geotransform
        self._plots: list[Plot] = []
        self._colors = ColorManager(colormap_name=colormap_name, ncolors=ncolors)
        self._plot_count: NameQueue = NameQueue()
        super().__init__()

    def get_all_ids(self) -> list[UUID]:
        return [i.id for i in self._plots]

    def create_plot(
        self,
        id: UUID,
        name: str | None = None,
        starts_visible: bool = True,
    ) -> None:
        color = self._colors.acquire(id)
        if name is None:
            name = self._plot_count.next()
        plot = Plot(id, name, color, starts_visible)
        self._plots.append(plot)
        self.plot_created.emit(plot.id)

    def update_plot(
        self, id: UUID, data: np.ndarray, data_input_type: DataInputType
    ) -> None:
        plot = self.get_plot_from_id(id)
        setattr(plot.data, data_input_type, data)
        self.plot_updated.emit(id, data_input_type)

    def rename_plot(self, id: UUID, name: str) -> None:
        plot = self.get_plot_from_id(id)
        plot.name = name
        self.plot_renamed.emit(id, name)

    def remove_plot(self, id: UUID) -> None:
        try:
            plot = next(i for i in self._plots if i.id == id)
        except StopIteration:
            raise StopIteration(f"{id} has not been added, so it cannot be removed.")
        self._plots.remove(plot)
        self._plot_count.add_to(plot._original_name)
        self._colors.release(id)
        self.plot_removed.emit(plot.id)

    def get_plot_from_id(self, id: UUID) -> Plot:
        if not any(i.id == id for i in self._plots):
            raise RuntimeError(f"Plot ({id}) does not exist.")
        return next(i for i in self._plots if i.id == id)

    def reset(self) -> None:
        for id in self.get_all_ids():
            self.remove_plot(id)

    def save_all_plots(self, save_directory: Path) -> None:
        spec_model_list: dict[str, FullSpectrumModel | SpectrumArea] = {}
        for id in self.get_all_ids():
            plot = self.get_plot_from_id(id)
            spectral_data = plot.data.require_vector()
            pixel_data = plot.data.require_pixel()
            if plot.data.is_point:
                specmodel = FullSpectrumModel.build(
                    spectral_data, pixel_data, plot.id, geotransform=self.gtrans
                )
            else:
                bulk_data = plot.data.require_bulk()
                specmodel = SpectrumArea.build(
                    plot.name,
                    spectral_data,
                    bulk_data,
                    pixel_data,
                    plot.id,
                    geotransform=self.gtrans,
                )
            spec_model_list[plot.name] = specmodel

        for name, specinfo in spec_model_list.items():
            write_spectrum(specinfo, save_directory=save_directory, save_name=name)
