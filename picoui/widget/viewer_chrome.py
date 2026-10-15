"""Shared toolbar / readout helpers for DiffractionLab and Reflection Viewer."""

from __future__ import annotations

from collections.abc import Callable
from typing import Tuple

from picoui.icons import IconRegistry
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget


def icon_from_registry(icon_key: str) -> QIcon:
    """Return an :class:`QIcon` for *icon_key* (may be empty)."""
    if not icon_key:
        return QIcon()
    return IconRegistry.get_icon_safe(icon_key)


def icon_label(
    icon_key: str,
    text: str,
    *,
    margin_right: int = 12,
    icon_size: int = 16,
) -> Tuple[QWidget, QLabel]:
    """Build a small icon + text host widget.

    :param icon_key: IconRegistry / qtawesome identifier (empty skips icon).
    :param text: Initial label text.
    :param margin_right: Right margin on the host layout.
    :param icon_size: Pixmap edge length in pixels.
    :returns: ``(host, text_label)`` where *text_label* is mutable.
    """
    host = QWidget()
    row = QHBoxLayout(host)
    row.setContentsMargins(0, 0, margin_right, 0)
    row.setSpacing(4)
    if icon_key:
        icon = QLabel()
        icon.setPixmap(icon_from_registry(icon_key).pixmap(icon_size, icon_size))
        row.addWidget(icon)
    label = QLabel(text)
    row.addWidget(label)
    return host, label


def standard_zoom_actions(
    parent: QWidget,
    *,
    on_zoom_in: Callable[[], None],
    on_zoom_out: Callable[[], None],
    on_reset: Callable[[], None],
    zoom_in_tip: str = "Zoom in (mouse wheel also works)",
    zoom_out_tip: str = "Zoom out (mouse wheel also works)",
    reset_tip: str = "Fit the view to the window",
) -> Tuple[QAction, QAction, QAction]:
    """Create Zoom In / Out / Reset actions with shared shortcuts and icons.

    Shortcuts: ``Ctrl+=``, ``Ctrl+-``, ``Ctrl+0``.

    :param parent: Parent for the :class:`QAction` instances.
    :param on_zoom_in: Slot for Zoom In.
    :param on_zoom_out: Slot for Zoom Out.
    :param on_reset: Slot for Reset Zoom.
    :returns: ``(zoom_in, zoom_out, reset_zoom)`` actions.
    """
    zoom_in = QAction(
        icon_from_registry(IconRegistry.ZOOM_IN),
        "Zoom &In",
        parent,
    )
    zoom_in.setShortcut(QKeySequence("Ctrl+="))
    zoom_in.setStatusTip(zoom_in_tip)
    zoom_in.triggered.connect(on_zoom_in)

    zoom_out = QAction(
        icon_from_registry(IconRegistry.ZOOM_OUT),
        "Zoom &Out",
        parent,
    )
    zoom_out.setShortcut(QKeySequence("Ctrl+-"))
    zoom_out.setStatusTip(zoom_out_tip)
    zoom_out.triggered.connect(on_zoom_out)

    reset = QAction(
        icon_from_registry(IconRegistry.FIT_TO_PAGE),
        "&Reset Zoom",
        parent,
    )
    reset.setShortcut(QKeySequence("Ctrl+0"))
    reset.setStatusTip(reset_tip)
    reset.triggered.connect(on_reset)

    return zoom_in, zoom_out, reset
