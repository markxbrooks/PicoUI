from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QGroupBox, QLabel

from PySide6.QtCore import Qt

from PySide6.QtGui import QFont, QFontInfo, QPixmap

from picoui.helpers.layout import create_progress_bar, create_layout_with_items
from picoui.splash.config import SplashScreenConfig


class SplashScreen(QWidget):

    def __init__(self, config: SplashScreenConfig):
        super().__init__()

        self.config = config
        self.progress_bar: QProgressBar | None = None

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
        group_layout = group.layout()

        group_layout.addWidget(self._create_logo())
        if self.config.show_progress:
            group_layout.addLayout(self._create_progress_bar())
        group_layout.addWidget(self._create_subtitle())

        layout.addWidget(group)

    def _create_group(self) -> QGroupBox:
        """Create the titled group box that holds logo, progress, and subtitle."""
        group_box = QGroupBox(self.config.title or __program__)
        group_box.setAlignment(Qt.AlignHCenter)

        # Title styling
        font_size = self.config.theme.title_size
        preferred_fonts = self.config.theme.title_font
        for font_name in preferred_fonts:
            font = QFont(font_name, font_size)
            font.setBold(True)
            if QFontInfo(font).family() == font_name:
                group_box.setFont(font)
                break

        group_box.setStyleSheet(
            f"color: {self.config.foreground_color}; font-weight: bold;"
        )

        group_layout = QVBoxLayout()
        group_layout.setAlignment(Qt.AlignCenter)
        group_box.setLayout(group_layout)
        return group_box

    def _create_logo(self) -> QLabel:
        """Create the logo label."""
        label = QLabel()
        label.setAlignment(Qt.AlignCenter)

        if self.config.logo_path:
            pixmap = QPixmap(self.config.logo_path).scaled(
                *self.config.logo_size.to_tuple(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            label.setPixmap(pixmap)

        return label

    def _create_progress_bar(self) -> QVBoxLayout:
        """Create the progress bar layout and assign the instance bar."""
        self.progress_bar = create_progress_bar()
        progress_container = create_layout_with_items(
            items=[self.progress_bar],
            start_stretch=True,
            end_stretch=True,
        )
        return progress_container

    def _create_subtitle(self) -> QLabel:
        """Create the subtitle label."""
        label = QLabel(self.config.subtitle)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setMinimumHeight(80)
        label.setFixedSize(
            self.config.dimensions.width - 25,
            80,
        )

        label.setStyleSheet(
            "QLabel{"
            f"color: {self.config.foreground_color};"
            f"font-family: '{self.config.subtitle_font_family}';"
            f"font-size: {self.config.subtitle_font_size}px;"
            "}"
        )
        return label