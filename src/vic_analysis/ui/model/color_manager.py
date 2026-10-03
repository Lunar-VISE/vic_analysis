from collections import deque
from uuid import UUID

from cmap import Color, Colormap


class ColorManager:
    def __init__(self, colormap_name: str = "seaborn:tab20", ncolors: int = 20) -> None:
        clrmap = Colormap(colormap_name)
        self._available: deque[Color] = deque(
            [clrmap(i % ncolors) for i in range(ncolors)]
        )
        self._assigned: dict[UUID, Color] = {}

    def acquire(self, plot_id: UUID) -> Color:
        if plot_id in self._assigned:
            return self._assigned[plot_id]

        if not self._available:
            raise RuntimeError("No Colors Available")

        color = self._available.popleft()
        self._assigned[plot_id] = color
        return color

    def release(self, plot_id: UUID) -> None:
        self._validate_assignment(plot_id)
        color = self._assigned.pop(plot_id)
        self._available.appendleft(color)

    def color_for(self, plot_id: UUID) -> Color:
        self._validate_assignment(plot_id)
        return self._assigned[plot_id]

    def _validate_assignment(self, plot_id: UUID) -> None:
        if plot_id not in self._assigned:
            raise RuntimeError(f"{plot_id} has not been assigned")
