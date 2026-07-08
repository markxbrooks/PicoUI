"""
This module provides functionality for setting up and displaying a splash
screen for a given application. It includes progress updates to simulate
a loading process.

Functions:
- setup_splash_screen: Sets up and animates a splash screen for a given
  application.
"""
from picoui.dimensions import Dimensions
from picoui.splash.config import SplashScreenConfig
from picoui.splash.screen import SplashScreen


def setup_splash_screen(app, config: SplashScreenConfig):
    """Sets up and animates a splash screen for a given application."""
    splash = create_splash_screen(config)
    splash.show()
    splash.raise_()  # Ensure the splash screen is raised
    splash.activateWindow()  # Activate the splash screen window
    import time

    for i in range(101):
        splash.progress_bar.setValue(i)
        app.processEvents()
        time.sleep(0.03)
    splash.close()


def create_splash_screen(config: SplashScreenConfig,
                         dimensions: Dimensions = Dimensions(width=500, height=400)) -> SplashScreen:
    """create splash screen (Qt) for the ElMo application."""
    splash = SplashScreen(config)
    splash.setFixedSize(*dimensions.to_tuple())
    splash.setStyleSheet(config.style)
    return splash