"""
Centralized theme management for PicoUI hosts.

Applies qdarktheme (when available), optional custom stylesheets, and
consistent widget styling across applications.
"""

from __future__ import annotations

from typing import Optional

from decologr import Decologr as log
from PySide6.QtCore import QObject
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QWidget

try:
    import darkdetect

    HAS_DARKDETECT = True
except ImportError:
    HAS_DARKDETECT = False

try:
    import qdarktheme

    HAS_QDARKTHEME = True
except ImportError:
    HAS_QDARKTHEME = False


class ThemeType:
    """Supported theme modes."""

    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


class ThemeManager(QObject):
    """Singleton theme manager for PicoUI applications."""

    _instance: Optional["ThemeManager"] = None
    Theme: type[ThemeType] = ThemeType

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        super().__init__()
        self._initialized = True
        self._theme: str = ThemeType.AUTO
        self._resolved: str = ThemeType.DARK
        self._corner_shape: str = "rounded"
        self._custom_applied: bool = False

    @property
    def theme(self) -> str:
        """Last requested theme mode (may be ``auto``)."""
        return self._theme

    @property
    def resolved_theme(self) -> str:
        """Concrete light/dark theme currently in effect."""
        return self._resolved

    @staticmethod
    def detect() -> str:
        """Return ``light`` or ``dark`` from the OS, defaulting to dark."""
        if not HAS_DARKDETECT:
            return ThemeType.DARK
        try:
            return ThemeType.DARK if darkdetect.isDark() else ThemeType.LIGHT
        except Exception:
            log.warning("Theme detection failed, defaulting to dark")
            return ThemeType.DARK

    @staticmethod
    def resolve(theme: str = ThemeType.AUTO) -> str:
        """Resolve ``auto`` to a concrete light/dark value."""
        if theme == ThemeType.AUTO:
            return ThemeManager.detect()
        if theme in (ThemeType.LIGHT, ThemeType.DARK):
            return theme
        log.warning(f"Unknown theme {theme!r}, defaulting to dark")
        return ThemeType.DARK

    @staticmethod
    def stylesheet(theme: str = ThemeType.AUTO, corner_shape: str = "rounded") -> str:
        """Return a qdarktheme stylesheet, or an empty string if unavailable."""
        if not HAS_QDARKTHEME or not hasattr(qdarktheme, "load_stylesheet"):
            return ""
        resolved = ThemeManager.resolve(theme)
        try:
            return qdarktheme.load_stylesheet(resolved, corner_shape=corner_shape)
        except TypeError:
            return qdarktheme.load_stylesheet(resolved)
        except Exception as ex:
            log.error(f"Error loading qdarktheme stylesheet: {ex}")
            return ""

    @staticmethod
    def palette(theme: str = ThemeType.AUTO) -> QPalette | None:
        """Return a qdarktheme palette, or ``None`` if unavailable."""
        if not HAS_QDARKTHEME or not hasattr(qdarktheme, "load_palette"):
            return None
        resolved = ThemeManager.resolve(theme)
        try:
            return qdarktheme.load_palette(resolved)
        except Exception as ex:
            log.error(f"Error loading qdarktheme palette: {ex}")
            return None

    @staticmethod
    def apply_theme(
        theme: str = ThemeType.DARK,
        corner_shape: str = "rounded",
    ) -> bool:
        """
        Apply qdarktheme to the application.

        :param theme: ``auto``, ``light``, or ``dark``
        :param corner_shape: qdarktheme corner shape (``rounded`` or ``sharp``)
        :return: True if a theme was applied
        """
        manager = ThemeManager()
        manager._theme = theme
        manager._corner_shape = corner_shape
        resolved = ThemeManager.resolve(theme)
        manager._resolved = resolved

        if not HAS_QDARKTHEME:
            log.debug("qdarktheme not available, skipping theme application")
            return False

        try:
            app = QApplication.instance()
            if not app:
                log.warning("No QApplication instance found for theme application")
                return False

            manager._custom_applied = False

            if hasattr(qdarktheme, "setup_theme"):
                try:
                    qdarktheme.setup_theme(theme, corner_shape=corner_shape)
                except TypeError:
                    qdarktheme.setup_theme(theme)
                log.info(f"qdarktheme applied: {theme} (resolved {resolved})")
                return True

            if hasattr(qdarktheme, "load_stylesheet"):
                stylesheet = ThemeManager.stylesheet(theme, corner_shape=corner_shape)
                if stylesheet:
                    app.setStyleSheet(stylesheet)
                palette = ThemeManager.palette(theme)
                if palette is not None:
                    app.setPalette(palette)
                log.info(f"qdarktheme applied via stylesheet: {resolved}")
                return True

            log.warning("qdarktheme API not recognized")
            return False
        except Exception as ex:
            log.error(f"Error applying qdarktheme: {ex}")
            return False

    @staticmethod
    def apply_style(widget: QWidget, style: str) -> None:
        """Apply a stylesheet string to a widget."""
        if widget:
            widget.setStyleSheet(style)

    @staticmethod
    def apply_table_style(widget: QWidget) -> None:
        """Apply charcoal embossed table styling."""
        table_style = """
            QTableWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 8px;
                gridline-color: #2a2a2a;
                color: #ffffff;
                selection-background-color: #3a3a3a;
                selection-color: #ffffff;
            }

            QTableWidget::item {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a,
                    stop:0.5 #252525,
                    stop:1 #1f1f1f);
                border: 1px solid #1a1a1a;
                border-radius: 4px;
                padding: 4px;
                color: #ffffff;
            }

            QTableWidget::item:selected {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3a3a3a,
                    stop:0.5 #353535,
                    stop:1 #2f2f2f);
                border: 1px solid #4a4a4a;
            }

            QTableWidget::item:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #323232,
                    stop:0.5 #2d2d2d,
                    stop:1 #282828);
                border: 1px solid #3a3a3a;
            }

            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a,
                    stop:1 #1f1f1f);
                color: #ffffff;
                padding: 6px;
                border: 1px solid #1a1a1a;
                border-radius: 4px;
                font-weight: bold;
            }

            QTableCornerButton::section {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 8px 0 0 0;
            }
        """
        ThemeManager.apply_style(widget, table_style)

    @staticmethod
    def get_custom_stylesheet() -> str:
        """Palette-based extras that complement qdarktheme."""
        font_family = "Consolas, 'Courier New', monospace"
        return f"""
        QWidget {{
            font-family: {font_family};
        }}

        QTableView {{
            gridline-color: palette(mid);
            selection-background-color: palette(highlight);
            selection-color: palette(highlighted-text);
            alternate-background-color: palette(alternate-base);
            border: 1px solid palette(mid);
            border-radius: 8px;
            padding: 4px;
        }}

        QHeaderView::section {{
            background-color: palette(button);
            padding: 8px 12px;
            border: 1px solid palette(mid);
            border-radius: 6px;
            font-weight: bold;
            margin: 2px;
        }}

        QTableView::item {{
            padding: 4px;
            border-radius: 4px;
        }}

        QTableView::item:selected {{
            background-color: palette(highlight);
            color: palette(highlighted-text);
        }}

        QPushButton {{
            min-height: 20px;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid palette(mid);
            font-weight: 500;
        }}

        QPushButton:hover {{
            border: 1px solid palette(highlight);
        }}

        QTabWidget::pane {{
            border: 1px solid palette(mid);
            border-radius: 8px;
            padding: 4px;
            background-color: palette(base);
        }}

        QTabBar::tab {{
            padding: 10px 16px;
            margin-right: 4px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            border: 1px solid palette(mid);
            border-bottom: none;
            background-color: palette(button);
            min-width: 80px;
        }}

        QTabBar::tab:selected {{
            background-color: palette(base);
            border-bottom: 2px solid palette(highlight);
            font-weight: bold;
        }}

        QStatusBar {{
            border-top: 1px solid palette(mid);
            background-color: palette(window);
            padding: 4px;
        }}

        QDialog {{
            background-color: palette(window);
            border-radius: 12px;
        }}

        QDialogButtonBox {{
            spacing: 8px;
            padding: 8px;
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            border: 1px solid palette(mid);
            border-radius: 6px;
            padding: 6px 10px;
            background-color: palette(base);
            color: palette(text);
            selection-background-color: palette(highlight);
            selection-color: palette(highlighted-text);
        }}

        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid palette(highlight);
        }}

        QComboBox {{
            border: 1px solid palette(mid);
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 20px;
        }}

        QComboBox:hover {{
            border: 1px solid palette(highlight);
        }}

        QComboBox::drop-down {{
            border: none;
            border-left: 1px solid palette(mid);
            border-top-right-radius: 6px;
            border-bottom-right-radius: 6px;
            width: 20px;
        }}

        QComboBox QAbstractItemView {{
            border: 1px solid palette(mid);
            border-radius: 6px;
            selection-background-color: palette(highlight);
            selection-color: palette(highlighted-text);
            padding: 4px;
        }}

        QCheckBox, QRadioButton {{
            spacing: 8px;
            padding: 4px;
        }}

        QGroupBox {{
            border: 1px solid palette(mid);
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: bold;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            background-color: palette(window);
        }}

        QScrollBar:vertical {{
            border: none;
            background-color: palette(base);
            width: 12px;
            margin: 0;
            border-radius: 6px;
        }}

        QScrollBar::handle:vertical {{
            background-color: palette(mid);
            min-height: 30px;
            border-radius: 6px;
            margin: 2px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: palette(highlight);
        }}

        QScrollBar:horizontal {{
            border: none;
            background-color: palette(base);
            height: 12px;
            margin: 0;
            border-radius: 6px;
        }}

        QScrollBar::handle:horizontal {{
            background-color: palette(mid);
            min-width: 30px;
            border-radius: 6px;
            margin: 2px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: palette(highlight);
        }}

        QSpinBox, QDoubleSpinBox {{
            border: 1px solid palette(mid);
            border-radius: 6px;
            padding: 4px 8px;
            min-height: 24px;
        }}

        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid palette(highlight);
        }}

        QListWidget, QTreeWidget {{
            border: 1px solid palette(mid);
            border-radius: 8px;
            padding: 4px;
        }}

        QListWidget::item, QTreeWidget::item {{
            padding: 4px;
            border-radius: 4px;
        }}

        QListWidget::item:selected, QTreeWidget::item:selected {{
            background-color: palette(highlight);
            color: palette(highlighted-text);
        }}

        QMenuBar {{
            background-color: palette(window);
            border-bottom: 1px solid palette(mid);
            padding: 4px;
            spacing: 8px;
        }}

        QMenuBar::item {{
            padding: 6px 12px;
            border-radius: 4px;
        }}

        QMenuBar::item:selected {{
            background-color: palette(highlight);
            color: palette(highlighted-text);
        }}

        QMenu {{
            border: 1px solid palette(mid);
            border-radius: 6px;
            padding: 4px;
        }}

        QMenu::item {{
            padding: 6px 24px;
            border-radius: 4px;
        }}

        QMenu::item:selected {{
            background-color: palette(highlight);
            color: palette(highlighted-text);
        }}

        QMenu::separator {{
            height: 1px;
            background-color: palette(mid);
            margin: 4px 8px;
        }}
        """

    @staticmethod
    def apply_custom_stylesheet() -> bool:
        """Append PicoUI custom CSS to the current application stylesheet."""
        try:
            app = QApplication.instance()
            if not app:
                log.warning("No QApplication instance found for stylesheet application")
                return False

            custom_css = ThemeManager.get_custom_stylesheet()
            manager = ThemeManager()
            if manager._custom_applied:
                return True
            current = app.styleSheet()
            if current:
                app.setStyleSheet(current + custom_css)
            else:
                app.setStyleSheet(custom_css)
            log.info("Custom stylesheet applied")
            manager._custom_applied = True
            return True
        except Exception as ex:
            log.error(f"Error applying custom stylesheet: {ex}")
            return False

    @staticmethod
    def initialize(
        theme: str = ThemeType.AUTO,
        apply_custom: bool = True,
        apply_qdarktheme: bool = True,
        corner_shape: str = "rounded",
    ) -> bool:
        """
        Initialize the theme system.

        :param theme: ``auto``, ``light``, or ``dark``
        :param apply_custom: Whether to append PicoUI custom CSS
        :param apply_qdarktheme: Whether to apply qdarktheme
        :param corner_shape: qdarktheme corner shape
        :return: True if requested steps succeeded
        """
        success = True
        if apply_qdarktheme:
            success = ThemeManager.apply_theme(theme, corner_shape=corner_shape)
        if apply_custom:
            success = ThemeManager.apply_custom_stylesheet() and success
        return success

    @staticmethod
    def get_progress_bar_style(use_custom_colors: bool = False) -> str:
        """Progress-bar stylesheet; splash screens typically use custom colors."""
        if use_custom_colors:
            return """
            QProgressBar {
                background-color: rgb(82, 64, 157);
                color: #fff;
                border-style: none;
                border-radius: 10px;
                text-align: center;
                height: 50px;
            }

            QProgressBar::chunk {
                border-radius: 10px;
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0.711364,
                    x2:1, y2:0.523,
                    stop:0 rgba(0, 0, 199, 255),
                    stop:1 rgba(170, 85, 255, 255)
                );
            }
            """
        return """
            QProgressBar {
                background-color: palette(mid);
                color: palette(text);
                border-style: none;
                border-radius: 10px;
                text-align: center;
                height: 20px;
                min-width: 300px;
            }

            QProgressBar::chunk {
                border-radius: 10px;
                background: qlineargradient(
                    spread:pad,
                    x1:0, y1:0.5,
                    x2:1, y2:0.5,
                    stop:0 palette(highlight),
                    stop:1 palette(highlight)
                );
            }
            """
