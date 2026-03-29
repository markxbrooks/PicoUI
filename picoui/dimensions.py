"""
PicoUI Dimensions
"""

from PySide6.QtCore import QSize

class Dimensions:
    """Dimensions"""
    WIDTH = 100
    HEIGHT = 100
    MIN_HEIGHT = 100
    MAX_HEIGHT = 100
    MIN_WIDTH = 100
    MAX_WIDTH = 100
    FONT_PT = 10


class PicoUiDimensions:
    """PicoUiDimensions"""

    ICON_SIZE = QSize(40, 40)
    PROGRESS_BAR = {"width": 500, "height": 30}
    DIALOG = {"width": 500, "height": 120}
