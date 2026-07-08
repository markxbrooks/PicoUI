from PySide6.QtWidgets import QWidget, QVBoxLayout

from PySide6.QtCore import Qt
from picoui.splash.config import SplashScreenConfig


class SplashScreen(QWidget):

    def __init__(self, config: SplashScreenConfig):
        super().__init__()

        self.config = config
        self.progress_bar = None

        self._build_ui()

    def _build_ui(self):
        self.setWindowFlags(
            Qt.SplashScreen |
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        self.setFixedSize(*self.config.dimensions.to_tuple())
        self.setStyleSheet(
            f"background-color: {self.config.background_color};"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(self.config.spacing)

        group = self._create_group()

        group.layout().addWidget(self._create_logo())
        group.layout().addLayout(self._create_progress_bar())
        group.layout().addWidget(self._create_subtitle())

        layout.addWidget(group)