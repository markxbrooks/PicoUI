"""
Splash screen setup and progress animation helpers.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from picoui.splash.config import SplashScreenConfig
from picoui.splash.screen import SplashScreen

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


def create_splash_screen(config: SplashScreenConfig) -> SplashScreen:
    """Create a splash screen widget from *config*."""
    return SplashScreen(config)


def animate_splash_progress(
    splash: SplashScreen,
    app: QApplication,
    *,
    steps: int = 101,
    delay: float = 0.03,
) -> None:
    """Animate the splash progress bar from 0 to 100."""
    if splash.progress_bar is None:
        return
    for value in range(steps):
        splash.progress_bar.setValue(value)
        app.processEvents()
        time.sleep(delay)


def setup_splash_screen(app: QApplication, config: SplashScreenConfig) -> None:
    """Set up, animate, and close a splash screen for *app*."""
    splash = create_splash_screen(config)
    splash.show()
    splash.raise_()
    splash.activateWindow()
    animate_splash_progress(splash, app)
    splash.close()
