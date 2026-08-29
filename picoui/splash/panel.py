"""Shared JDXI-style splash panel layout (card, labels, optional progress)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget

from picoui.helpers.layout import create_layout_with_items
from picoui.splash.config import SplashScreenConfig
from picoui.splash.styles import SPLASH_CONTENT_SPACING, SPLASH_PROGRESS_WIDTH_INSET
from picoui.widget.helper import create_logo_label_from_spec


@dataclass(slots=True)
class SplashPanelWidgets:
    """Widgets created by :func:`build_jdxi_splash_panel`."""

    card: QFrame
    progress_bar: QProgressBar | None
    status_label: QLabel | None
    title_label: QLabel


def build_jdxi_splash_panel(
    parent: QWidget,
    config: SplashScreenConfig,
    *,
    show_progress: bool | None = None,
    show_status: bool | None = None,
) -> SplashPanelWidgets:
    """
    Build the JDXI card panel on *parent*.

    Returns the card frame and key child widgets. The title label is created
    parented to *parent* for overlay positioning by the caller.
    """
    include_progress = config.show_progress if show_progress is None else show_progress
    include_status = bool(config.status_text) if show_status is None else show_status

    card = QFrame(parent)
    card.setObjectName("Card")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(0, 0, 0, 0)
    card_layout.setSpacing(SPLASH_CONTENT_SPACING)

    logo = create_logo_label_from_spec(config.logo)
    logo.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    card_layout.addWidget(logo)

    progress_bar: QProgressBar | None = None
    if include_progress:
        progress_bar = QProgressBar(card)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setFixedWidth(config.dimensions.width - SPLASH_PROGRESS_WIDTH_INSET)
        card_layout.addLayout(
            create_layout_with_items(
                items=[progress_bar],
                start_stretch=True,
                end_stretch=True,
            )
        )

    status_label: QLabel | None = None
    if include_status:
        status_label = QLabel(config.status_text, card)
        status_label.setObjectName("StatusLabel")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(status_label)

    subtitle_text = config.subtitle.label or ""
    if subtitle_text:
        subtitle = QLabel(subtitle_text, card)
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setAlignment(
            config.subtitle.alignment or Qt.AlignmentFlag.AlignCenter
        )
        subtitle.setWordWrap(config.subtitle.word_wrap)
        card_layout.addWidget(subtitle)

    if config.credits_text:
        credits = QLabel(config.credits_text, card)
        credits.setObjectName("CreditLabel")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setWordWrap(True)
        card_layout.addWidget(credits)

    title_label = QLabel(config.title, parent)
    title_label.setObjectName("TitleLabel")

    return SplashPanelWidgets(
        card=card,
        progress_bar=progress_bar,
        status_label=status_label,
        title_label=title_label,
    )
