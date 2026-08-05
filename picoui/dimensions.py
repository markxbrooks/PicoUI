"""
PicoUI Dimensions
"""
from dataclasses import dataclass

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QVBoxLayout


@dataclass
class Dimensions:
    """Dimensions of the UI (width, height, and radius, radius, point_size"""
    width: int = 100
    height: int = 100
    min_height: int = 100
    max_height: int = 100
    min_width: int = 100
    max_width: int = 100
    radius: int = 10
    point_size: int = 5
    line_width: float = 1.2
    spacing: int = 10
    margin: int = 5

    @property
    def size(self) -> tuple[int, int]:
        return self.width, self.height

    @property
    def margins(self):
        return self.margin, self.margin, self.margin, self.margin

    def to_tuple(self) -> tuple[int, int]:
        return self.width, self.height


class PicoUiDimensions:
    """PicoUiDimensions"""

    ICON_SIZE = QSize(40, 40)
    PROGRESS_BAR = {"width": 500, "height": 30}
    DIALOG = {"width": 500, "height": 120}


def update_layout_with_dimensions(layout: QVBoxLayout | QVBoxLayout, window_dimensions: Dimensions):
    """update layout with dimensions"""
    layout.setContentsMargins(*window_dimensions.margins)
    layout.setSpacing(window_dimensions.spacing)
