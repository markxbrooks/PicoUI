"""
PicoUI Dimensions
"""
from dataclasses import dataclass

from PySide6.QtCore import QSize


@dataclass
class Dimensions:
    """Dimensions"""
    width = 100
    height = 100
    min_height = 100
    max_height = 100
    min_width = 100
    max_width = 100
    radius = 10
    point_size = 5
    line_width = 1.2


class PicoUiDimensions:
    """PicoUiDimensions"""

    ICON_SIZE = QSize(40, 40)
    PROGRESS_BAR = {"width": 500, "height": 30}
    DIALOG = {"width": 500, "height": 120}
