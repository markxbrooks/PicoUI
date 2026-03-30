from dataclasses import dataclass


@dataclass
class Separator:
    """Insert a separator when building menus or toolbars from layout."""


@dataclass
class SubMenu:
    """Nested menu with a recursive item list (same entry types as top-level)."""

    title: str
    items: list


@dataclass
class RecentFilesMenu:
    """``build_menu`` inserts ``ElMoWindow.recent_files_menu`` (filled by ``_refresh_recent_files_menu``)."""
