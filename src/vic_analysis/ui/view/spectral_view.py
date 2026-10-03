from importlib.resources import files
from uuid import UUID

import matplotlib.pyplot as plt
from matplotlib import patheffects
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseButton, MouseEvent, PickEvent
from matplotlib.lines import Line2D
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from vic_analysis.ui.model.artist_container import ArtistCollection, PlottedArtist
from vic_analysis.ui.model.plot_model import DataInputType, Plot, PlotModel
from vic_analysis.ui.view.widgets.data_context_menu import DataContextMenu
from vic_analysis.ui.view.widgets.zoom_canvas import ZoomCanvas, ZoomMode


class SpectralView(QWidget):
    def __init__(self, plot_model: PlotModel, parent: QWidget | None = None):
        super().__init__(parent)
        self._plot_model = plot_model
        self._artist_collection = ArtistCollection()
        self._hovered_artist: Line2D | None = None
        self.context_menu = DataContextMenu(self._plot_model, self)
        self._pending_context_menu: tuple[UUID, QPoint] | None = None

        with plt.style.context(
            str(files("vic_analysis").joinpath("resources/publications.mplstyle"))
        ):
            self.canvas = ZoomCanvas(remove_boundaries=False, mode=ZoomMode.PLOT)

        self.canvas.figure.set_frameon(True)
        self.canvas.figure.set_facecolor("#787878")

        self.axes: Axes = self.canvas.axes
        self.axes.set(xlabel="Wavelength (\u03bcm)", ylabel="Reflectance")

        self.setWindowTitle("Spectal View")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        self._plot_model.plot_updated.connect(self._on_plot_update)
        self._plot_model.plot_removed.connect(self._remove_line)
        self._plot_model.plot_hovered.connect(self._apply_path_effect)

        self.canvas.mpl_connect("pick_event", self._on_pick)
        self.canvas.mpl_connect("button_release_event", self._on_mouse_release)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _create_line(self, plot: Plot) -> None:
        (line,) = self.axes.plot(
            [0], [0], color=plot.color, lw=2, picker=5, label=plot.name
        )
        plt_art = PlottedArtist(line, plot.color, plot.id)
        self._artist_collection.add_plotted_artist(plt_art)
        self.axes.legend()
        self.canvas.draw_idle()

    def _remove_line(self, id: UUID) -> None:
        art = self._artist_collection.get_id(id)
        self._artist_collection.remove_plotted_artist(art)
        self._hovered_artist = None
        self.axes.legend()
        self.canvas.draw_idle()

    def _on_pick(self, event: PickEvent) -> None:
        mouse_event = event.mouseevent
        canvas_position = QPoint(
            int(mouse_event.x), self.canvas.height() - int(mouse_event.y)
        )
        global_position = self.mapToGlobal(canvas_position)
        match mouse_event.button:
            case MouseButton.RIGHT:
                plt_art = self._artist_collection.get_artist(event.artist)
                self._pending_context_menu = (plt_art.id, global_position)
            case _:
                return

    def _on_mouse_release(self, event) -> None:
        if event.button != MouseButton.RIGHT:
            return

        pending_menu = self._pending_context_menu
        self._pending_context_menu = None
        if pending_menu is not None and not self.canvas.right_dragged:
            plot_id, position = pending_menu
            self.context_menu.popup(plot_id, position)

    def _on_hover(self, event: MouseEvent) -> None:
        if event.inaxes is not self.axes:
            return

        # === Detect Which Line is being Hovered Over ===
        hovered_artist = next(
            (
                art
                for art in self.axes.get_children()
                if art.contains(event)[0] and isinstance(art, Line2D)
            ),
            None,
        )

        # === Detecting end of hover ===
        if (hovered_artist is None) and (self._hovered_artist is not None):
            id = self._artist_collection.get_artist(self._hovered_artist).id
            self._plot_model.plot_hovered.emit(id, False)
            self._hovered_artist = None

        # === Detecting start of hover ===
        if (hovered_artist is not None) and (self._hovered_artist is None):
            id = self._artist_collection.get_artist(hovered_artist).id
            self._plot_model.plot_hovered.emit(id, True)
            self._hovered_artist = hovered_artist

    def _apply_path_effect(self, id: UUID, hover_on: bool):
        hovered_artist = self._artist_collection.get_id(id).art
        if hover_on:
            hovered_artist.set_path_effects(
                [
                    patheffects.SimpleLineShadow(offset=(1, -1), alpha=0.25),
                    patheffects.Normal(),
                ]
            )
        else:
            hovered_artist.set_path_effects([])
        self.canvas.draw_idle()

    def _on_plot_update(self, id: UUID, data_input_type: DataInputType) -> None:
        plot = self._plot_model.get_plot_from_id(id)
        match data_input_type:
            case DataInputType.VECTOR:
                if not self._artist_collection.check_id(id):
                    self._create_line(plot)
                artist = self._artist_collection.get_id(id).art
                if isinstance(artist, Line2D):
                    artist.set_data(plot.data.require_vector().T)
                    self.axes.relim()
                    self.axes.autoscale()
                    self.canvas.update_data_limits()
                    self.canvas.update_plot()

    def _on_plot_rename(self, id: UUID, name: str) -> None:
        print("Plot Renamed!")
        artist = self._artist_collection.get_id(id).art
        artist.set_label(name)
        self.axes.legend()
        self.canvas.draw_idle()
