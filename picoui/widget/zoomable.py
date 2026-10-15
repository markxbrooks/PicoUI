"""Shared pan/zoom canvas used by ElMo Reflection Viewer and DiffractionLab."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QMouseEvent, QPainter, QWheelEvent
from PySide6.QtWidgets import QWidget


@dataclass
class ViewTransform:
    """World → widget pixel transform (shared by plots and image canvases)."""

    center_u: float = 0.0
    center_v: float = 0.0
    scale: float = 1.0  # screen pixels per world unit
    width: int = 1
    height: int = 1
    #: If True, world *v* increases upward (scientific plots). If False, down (images).
    flip_y: bool = True

    def world_to_screen(self, u: float, v: float) -> tuple[float, float]:
        """Map world coords to widget pixels (origin top-left)."""
        sx = (u - self.center_u) * self.scale + self.width * 0.5
        if self.flip_y:
            sy = self.height * 0.5 - (v - self.center_v) * self.scale
        else:
            sy = (v - self.center_v) * self.scale + self.height * 0.5
        return float(sx), float(sy)

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        """Map widget pixels to world coords."""
        u = (sx - self.width * 0.5) / self.scale + self.center_u
        if self.flip_y:
            v = (self.height * 0.5 - sy) / self.scale + self.center_v
        else:
            v = (sy - self.height * 0.5) / self.scale + self.center_v
        return float(u), float(v)

    def copy(self) -> "ViewTransform":
        """Return a shallow copy of this transform."""
        return ViewTransform(
            center_u=self.center_u,
            center_v=self.center_v,
            scale=self.scale,
            width=self.width,
            height=self.height,
            flip_y=self.flip_y,
        )


def fit_transform(
    u_min: float,
    u_max: float,
    v_min: float,
    v_max: float,
    width: int,
    height: int,
    *,
    padding: float = 0.08,
    flip_y: bool = True,
) -> ViewTransform:
    """Compute a transform that fits a world axis-aligned box into the widget."""
    width = max(int(width), 1)
    height = max(int(height), 1)
    if u_max <= u_min:
        u_max = u_min + 1.0
    if v_max <= v_min:
        v_max = v_min + 1.0
    span_u = u_max - u_min
    span_v = v_max - v_min
    u_min -= span_u * padding
    u_max += span_u * padding
    v_min -= span_v * padding
    v_max += span_v * padding
    span_u = u_max - u_min
    span_v = v_max - v_min
    scale = min(width / span_u, height / span_v)
    return ViewTransform(
        center_u=0.5 * (u_min + u_max),
        center_v=0.5 * (v_min + v_max),
        scale=float(scale),
        width=width,
        height=height,
        flip_y=flip_y,
    )


class ZoomableCanvas(QWidget):
    """QWidget base with Reflection-Viewer-style wheel zoom and hand pan.

    Interaction contract (shared look-and-feel):

    * Mouse wheel — zoom ×1.15 / ÷1.15, cursor-anchored
    * Left-drag — pan with open/closed hand cursor (short click still selects)
    * Middle-drag or Shift+Left-drag — pan immediately
    * :meth:`reset_view` / :meth:`zoom_in` / :meth:`zoom_out` — toolbar actions

    Subclasses implement :meth:`paint_contents` and optionally
    :meth:`fit_content_transform` / :meth:`on_left_click`.
    """

    view_changed = Signal()
    ZOOM_FACTOR = 1.15
    MIN_SCALE = 1e-3
    #: Pixels of left-button travel before a click becomes a hand-pan.
    PAN_DRAG_THRESHOLD_PX = 4.0

    def __init__(self, parent: QWidget | None = None, *, flip_y: bool = True) -> None:
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._transform = ViewTransform(flip_y=flip_y)
        self._drag_origin: QPointF | None = None
        self._drag_center: tuple[float, float] | None = None
        self._panning = False
        self._pending_left_pan = False
        self._background = QColor(30, 30, 34)
        self._set_idle_cursor()

    def transform(self) -> ViewTransform:
        """Return a copy of the current view transform."""
        return self._transform.copy()

    def is_panning(self) -> bool:
        """True while an active hand/middle pan drag is in progress."""
        return self._panning

    def set_background(self, color: QColor | str) -> None:
        """Set the canvas fill color behind content."""
        self._background = QColor(color)
        self.update()

    def reset_view(self) -> None:
        """Fit content into the widget (subclass supplies the bounds)."""
        fitted = self.fit_content_transform()
        if fitted is not None:
            self._transform = fitted
        self._sync_transform_size()
        self.update()
        self.view_changed.emit()

    def zoom_in(self) -> None:
        """Zoom in about the widget center (toolbar action)."""
        self._zoom_at(self.ZOOM_FACTOR, self.width() * 0.5, self.height() * 0.5)

    def zoom_out(self) -> None:
        """Zoom out about the widget center (toolbar action)."""
        self._zoom_at(1.0 / self.ZOOM_FACTOR, self.width() * 0.5, self.height() * 0.5)

    def fit_content_transform(self) -> ViewTransform | None:
        """Return a transform that fits domain content, or ``None`` to keep current."""
        return None

    def paint_contents(self, painter: QPainter, transform: ViewTransform) -> None:
        """Paint domain content in widget coordinates via *transform*."""

    def on_left_click(self, world_u: float, world_v: float, event: QMouseEvent) -> None:
        """Handle a plain left click in world coordinates (optional)."""

    def _set_idle_cursor(self) -> None:
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def _set_grab_cursor(self) -> None:
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def _begin_pan(self, origin: QPointF) -> None:
        self._drag_origin = QPointF(origin)
        self._drag_center = (
            self._transform.center_u,
            self._transform.center_v,
        )
        self._panning = True
        self._pending_left_pan = False
        self._set_grab_cursor()

    def _end_pan(self, *, emit_changed: bool) -> None:
        was_panning = self._panning
        self._drag_origin = None
        self._drag_center = None
        self._panning = False
        self._pending_left_pan = False
        self._set_idle_cursor()
        if was_panning and emit_changed:
            self.view_changed.emit()

    def _apply_pan_delta(self, pos: QPointF) -> None:
        if self._drag_origin is None or self._drag_center is None:
            return
        delta = pos - self._drag_origin
        scale = max(self._transform.scale, self.MIN_SCALE)
        self._transform.center_u = self._drag_center[0] - delta.x() / scale
        if self._transform.flip_y:
            self._transform.center_v = self._drag_center[1] + delta.y() / scale
        else:
            self._transform.center_v = self._drag_center[1] - delta.y() / scale
        self.update()

    def _sync_transform_size(self) -> None:
        self._transform.width = max(self.width(), 1)
        self._transform.height = max(self.height(), 1)

    def _zoom_at(self, factor: float, sx: float, sy: float) -> None:
        wu, wv = self._transform.screen_to_world(sx, sy)
        self._transform.scale = max(self.MIN_SCALE, self._transform.scale * factor)
        su, sv = self._transform.world_to_screen(wu, wv)
        if self._transform.flip_y:
            du = (sx - su) / self._transform.scale
            dv = (sv - sy) / self._transform.scale
            self._transform.center_u -= du
            self._transform.center_v -= dv
        else:
            self._transform.center_u += (sx - su) / self._transform.scale
            self._transform.center_v += (sy - sv) / self._transform.scale
        self.update()
        self.view_changed.emit()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self._background)
        self._sync_transform_size()
        self.paint_contents(painter, self._transform)
        painter.end()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_transform_size()
        self.update()

    def enterEvent(self, event) -> None:  # noqa: N802
        super().enterEvent(event)
        if not self._panning:
            self._set_idle_cursor()

    def leaveEvent(self, event) -> None:  # noqa: N802
        super().leaveEvent(event)
        if not self._panning:
            self.unsetCursor()

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = self.ZOOM_FACTOR if delta > 0 else 1.0 / self.ZOOM_FACTOR
        pos = event.position()
        self._zoom_at(factor, pos.x(), pos.y())

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            self._begin_pan(event.position())
            return
        if event.button() == Qt.MouseButton.LeftButton:
            # Defer click vs pan until we see enough motion (hand grabber).
            self._drag_origin = QPointF(event.position())
            self._drag_center = (
                self._transform.center_u,
                self._transform.center_v,
            )
            self._pending_left_pan = True
            self._panning = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._pending_left_pan and self._drag_origin is not None:
            delta = event.position() - self._drag_origin
            if (
                abs(delta.x()) >= self.PAN_DRAG_THRESHOLD_PX
                or abs(delta.y()) >= self.PAN_DRAG_THRESHOLD_PX
            ):
                self._panning = True
                self._pending_left_pan = False
                self._set_grab_cursor()
        if not self._panning or self._drag_origin is None or self._drag_center is None:
            return
        self._apply_pan_delta(event.position())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() not in (
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.MiddleButton,
        ):
            return
        if self._pending_left_pan and not self._panning:
            # Treat as a click (Reflection Viewer selection, etc.).
            origin = self._drag_origin
            self._end_pan(emit_changed=False)
            if origin is not None:
                wu, wv = self._transform.screen_to_world(origin.x(), origin.y())
                self.on_left_click(wu, wv, event)
            return
        self._end_pan(emit_changed=True)
