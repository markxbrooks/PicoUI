"""Reusable Matplotlib figure/canvas widget for Qt."""

from __future__ import annotations

import logging

from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from picoui.matplotlib import AxesConfig
from picoui.matplotlib.config import AxesConfig
from PySide6.QtWidgets import QVBoxLayout, QWidget

logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.backends").setLevel(logging.WARNING)
logging.getLogger("matplotlib.backends.backend_qt5agg").setLevel(logging.WARNING)


def configure_axes(config: AxesConfig, ax: Axes | None = None):
    if config.x_config.limit is not None:
        ax.set_xlim(-config.x_config.limit, config.x_config.limit)
    if config.y_config.limit is not None:
        ax.set_ylim(-config.y_config.limit, config.y_config.limit)
    if config.visible:
        ax.set_axis_on()
    else:
        ax.set_axis_off()


class MatplotlibPlotWidget(QWidget):
    """Qt host for a Matplotlib ``Figure`` / ``FigureCanvas`` / ``Axes``.

    Subclasses supply domain-specific drawing; this base owns figure lifecycle,
    canvas redraw, optional axes styling via :class:`AxesConfig`, and export.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        figsize: tuple[float, float] = (10.0, 8.0),
        dpi: int = 100,
        axes_config: AxesConfig | None = None,
        add_canvas_to_layout: bool = True,
    ) -> None:
        super().__init__(parent)
        self.axes_config = axes_config or AxesConfig()
        self.figure = Figure(figsize=figsize, dpi=dpi)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.apply_axes_config()

        if add_canvas_to_layout:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.canvas)

    def apply_axes_config(self, config: AxesConfig | None = None) -> None:
        """Apply title / labels / limits / visibility from ``AxesConfig``."""
        cfg = config or self.axes_config
        self.axes_config = cfg
        x_font = cfg.x_config.font_config
        y_font = cfg.y_config.font_config
        title_font = cfg.title_config.font_config
        self.ax.set_xlabel(
            cfg.x_config.label,
            fontsize=x_font.size,
            fontweight=x_font.weight,
        )
        self.ax.set_ylabel(
            cfg.y_config.label,
            fontsize=y_font.size,
            fontweight=y_font.weight,
        )
        self.ax.set_title(
            cfg.title_config.label,
            fontsize=title_font.size,
            fontweight=title_font.weight,
        )
        configure_axes(cfg, self.ax)

    def redraw(self) -> None:
        self.canvas.draw()

    def export_figure(self, filename: str, *, dpi: int = 300) -> None:
        self.figure.savefig(filename, dpi=dpi, bbox_inches="tight")
