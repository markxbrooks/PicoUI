"""
Utility function for constructing absolute resource paths.

This module provides a function to determine the absolute path
of a resource file based on whether the program is being run
from a frozen state (e.g., packaged with PyInstaller) or a normal
environment.

Functions:
- resource_path: Returns the absolute path for a given resource file.

Example Usage:
==============
from picoui.resources import resource_path
image_path = resource_path(os.path.join("resources", "jdxi_cartoon_600.png"))
"""

import os
import sys


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)