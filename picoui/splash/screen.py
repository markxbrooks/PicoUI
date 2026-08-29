"""
A module to define a customizable splash screen widget.

This module provides a `SplashScreen` class, which creates a spec-driven splash
screen UI. It is designed to display a logo, subtitle, and optional progress bar,
with full support for configurable styles and dimensions. Additionally, it provides
helper functions for applying transparent styles to group box widgets.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QProgressBar, QVBoxLayout, QWidget

from picoui.helpers.layout import create_layout_with_items, create_progress_bar_from_spec
from picoui.splash.config import SplashScreenConfig, group_spec_from_config
from picoui.widget.helper import (
    apply_splash_subtitle_style,
    create_group_box_from_spec,
    create_label_from_spec,
    create_logo_label_from_spec,
)


def _is_transparent_background(color: str) -> bool:
    return color.strip().lower() == "transparent"


class SplashScreen(QWidget):
    """Spec-driven splash screen widget."""

    def __init__(self, config: SplashScreenConfig):
        super().__init__()
        self.config = config
        self.progress_bar: QProgressBar | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.SplashScreen
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setFixedSize(*self.config.dimensions.to_tuple())
        transparent = _is_transparent_background(self.config.background_color)
        if transparent:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet("background: transparent; color: white; font-size: 12px;")
        else:
            self.setStyleSheet(
                f"background-color: {self.config.background_color}; color: white; font-size: 12px;"
            )

        outer = create_layout_with_items(
            parent=self,
            items=[],
            vertical=True,
            start_stretch=False,
            end_stretch=False,
            spacing=self.config.spacing,
        )

        group_spec = self.config.group or group_spec_from_config(self.config)
        group, group_layout = create_group_box_from_spec(group_spec)
        if transparent:
            _apply_transparent_panel_style(group)

        logo = create_logo_label_from_spec(self.config.logo)
        if transparent:
            logo.setStyleSheet("background: transparent ;")
        else:
            logo.setStyleSheet("background: black; color: white; font-size: 12px;")
        group_layout.addWidget(logo)
        if self.config.show_progress:
            self.progress_bar = create_progress_bar_from_spec(self.config.progress)
            group_layout.addLayout(
                create_layout_with_items(
                    items=[self.progress_bar],
                    start_stretch=True,
                    end_stretch=True,
                )
            )

        subtitle = create_label_from_spec(self.config.subtitle_label_spec())
        apply_splash_subtitle_style(subtitle, self.config)
        group_layout.addWidget(subtitle)

        outer.addWidget(group)


def _apply_transparent_panel_style(widget: QGroupBox) -> None:
    """Remove opaque panel chrome so the splash shows through."""
    existing = widget.styleSheet() or ""
    widget.setStyleSheet(
        f"{existing} QGroupBox {{ background: transparent; border: none; color: white; font-size: 12px;}}"
    )
