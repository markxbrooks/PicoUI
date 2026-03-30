"""
Button Spec
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Optional

from PySide6.QtCore import Qt

from decologr import Decologr as log
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)


@dataclass
class UiNodeSpec:
    """Node with Children"""

    children: List["UiNodeSpec"] = field(default_factory=list)


@dataclass
class LeafSpec(UiNodeSpec):
    def __post_init__(self):
        if self.children:
            raise ValueError(f"{self.__class__.__name__} cannot have children")


@dataclass
class ButtonSpec:
    """Button Spec"""

    label: str = ""
    icon: str = ""
    tooltip: str = ""
    slot: Callable = None
    grouped: bool = False
    layout: QHBoxLayout | QVBoxLayout | None = None
    append_to: list | None = None
    name: str | None = None
    checkable: bool = True
    enabled: bool = True


@dataclass
class MessageBoxSpec(LeafSpec):
    """Message Box Spec"""

    title: str = ""
    message: str = ""
    type_attr: str = "Information"
    slot: Callable = None
    grouped: bool = False


@dataclass
class CheckBoxSpec(LeafSpec):
    """Button Spec"""

    label: str = ""
    tooltip: str = ""
    checked_state: bool = False
    slot: Callable = None
    style: str = None


@dataclass
class ComboBoxSpec(LeafSpec):
    """Button Spec"""

    items: list = field(default_factory=list)
    tooltip: str = ""
    slot: Callable | None = None


class FileSelectionMode(Enum):
    """File selection mode"""

    SAVE = "save"
    LOAD = "load"


@dataclass
class FileSelectionSpec(LeafSpec):
    """Qt file dialog configuration.

    Typical usage (open):

        spec = FileSelectionSpec(
            default_name=self.mtz_file_path or "",
            mode=FileSelectionMode.LOAD,
            filter=self.file_filters_data,
            caption="Open density map (MTZ)",
        )
        path, _selected_filter = get_file_load_from_spec(spec, parent=window)

    Pass a full path in ``default_name`` to re-open in that folder; set ``dir`` to
    force a starting directory. For a bare basename, ``default_name`` + ``file_type``
    builds the suggested path (e.g. ``name="out"``, ``file_type="pdb"`` → ``out.pdb``).
    """

    mode: FileSelectionMode | str = FileSelectionMode.SAVE
    file_type: str = "datasets"
    default_name: str = "datasets"
    caption: str = "Select datasets folder"
    filter: str = "All files (*.*)"
    dir: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.mode = _normalize_file_selection_mode(self.mode)


@dataclass
class TabSpec(UiNodeSpec):
    """Tab Spec"""

    name: str = ""
    icon: str | None = None
    widget_attr: str | None = None


@dataclass
class TabWidgetSpec(UiNodeSpec):
    """Tab Widget Spec"""

    name: str | None = None
    tabs: list[TabSpec] = field(default_factory=list)

    def __post_init__(self):
        self._tab_map = {t.name: t for t in self.tabs}

    def get_tab(self, name: str) -> TabSpec:
        return self._tab_map[name]


@dataclass
class IconSpec(LeafSpec):
    """IconSpec"""

    name: str = ""
    width: int = 40
    height: int = 40


@dataclass
class WindowSpec(UiNodeSpec):
    """WindowSpec"""

    title: str = ""
    icon: IconSpec = field(default_factory=IconSpec)
    width: int = 750
    height: int = 400


@dataclass
class SpinBoxSpec:
    """SpinBox Spec"""

    label: str = ""
    min_val: int = 1
    max_val: int = 127
    value: int = None
    tooltip: str = ""


_DIALOG_FUNCS = {
    FileSelectionMode.SAVE: QFileDialog.getSaveFileName,
    FileSelectionMode.LOAD: QFileDialog.getOpenFileName,
}


def wayland_safe_file_dialog_options():
    """
    Prefer Qt's non-native file dialog on Wayland.

    Native (e.g. portal/GTK) dialogs can trigger GLib GFileInfo icons warnings and
    xdg-shell protocol errors with some compositors, including when opened from
    a menu popup.
    """
    try:
        if os.environ.get("WAYLAND_DISPLAY"):
            return QFileDialog.Option.DontUseNativeDialog
        if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
            return QFileDialog.Option.DontUseNativeDialog
        app = QApplication.instance()
        if app is not None:
            name = (app.platformName() or "").lower()
            if name.startswith("wayland"):
                return QFileDialog.Option.DontUseNativeDialog
    except Exception:
        pass
    return None


def get_file_load_from_spec(spec: FileSelectionSpec, parent: QWidget) -> tuple[str, str]:
    """Open-file dialog; returns (path, selected_filter) like Qt."""
    mode = _normalize_file_selection_mode(spec.mode)
    func = _DIALOG_FUNCS.get(mode)
    if func is None:
        log.message(f"mode {spec.mode} unsupported")
        return "", ""

    start = _dialog_start_path(spec)
    opts = wayland_safe_file_dialog_options()
    kwargs = dict(
        caption=spec.caption,
        dir=start,
        filter=spec.filter,
    )
    if opts is not None:
        kwargs["options"] = opts
    return func(parent, **kwargs)


def get_file_save_from_spec(spec: FileSelectionSpec, parent: QWidget) -> tuple[str, str]:
    """Save-file dialog; returns (path, selected_filter) like Qt."""
    mode = _normalize_file_selection_mode(spec.mode)
    func = _DIALOG_FUNCS.get(mode)
    if func is None:
        log.message(f"mode {spec.mode} unsupported")
        return "", ""

    start = _dialog_start_path(spec)
    opts = wayland_safe_file_dialog_options()
    kwargs = dict(
        caption=spec.caption,
        dir=start,
        filter=spec.filter,
    )
    if opts is not None:
        kwargs["options"] = opts
    return func(parent, **kwargs)


def _dialog_start_path(spec: FileSelectionSpec) -> str:
    """Qt *dir* argument: explicit dir, else path-like default_name, else synthetic name."""
    if spec.dir:
        return spec.dir
    dn = (spec.default_name or "").strip()
    if not dn:
        return ""
    if os.path.isabs(dn) or os.sep in dn or (os.altsep and os.altsep in dn):
        return dn
    ext = (spec.file_type or "").strip().lstrip(".")
    if ext and not dn.lower().endswith(f".{ext.lower()}"):
        return f"{dn}.{ext}"
    return dn


def _normalize_file_selection_mode(mode: FileSelectionMode | str) -> FileSelectionMode | Any:
    """_normalize_file_selection_mode"""
    if isinstance(mode, FileSelectionMode):
        return mode
    if isinstance(mode, str):
        lowered = mode.strip().lower()
        if lowered == FileSelectionMode.SAVE.value:
            return FileSelectionMode.SAVE
        if lowered == FileSelectionMode.LOAD.value:
            return FileSelectionMode.LOAD
    return mode


@dataclass
class ActionSpec:
    """Declarative QAction fields for ``ElMoWindow.action_from_spec``."""

    text: str = ""
    icon: Optional[str] = None
    shortcut: Any = None
    status: str = ""
    triggered: Optional[Callable] = None
    toggled: Optional[Callable[[bool], None]] = None
    checkable: bool = False
    checked: Optional[bool] = None
    shortcut_context: Optional[Qt.ShortcutContext] = None
