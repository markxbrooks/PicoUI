"""
Configuration for a splash screen.

This class defines configurable attributes for designing and managing a splash
screen, including visual styles, dimensions, typography settings, and progress
indicator visibility.

Attributes:
    title (str): The text to display as the main title on the splash screen.
    subtitle (LabelSpec): A specification for the subtitle label on the splash
        screen. Defaults to an instance of LabelSpec.
    logo_path (str | None): The file path to the logo image to be displayed on
        the splash screen. If None, no logo is shown.
    style (str): The CSS style string applied to the splash screen container.
        Defaults to "background-color: black;".
    dimensions (Dimensions): The height and width of the splash screen window.
        Defaults to 500x400 dimensions.
    logo_size (Dimensions): The dimensions of the logo image displayed on the
        splash screen. Defaults to 250x150 dimensions.
    theme (SplashTheme): The visual theme applied to the splash screen.
        Defaults to an instance of SplashTheme.
    title_font_family (tuple[str, ...]): The font family to be used for the
        title text. Provides a fallback sequence if a font is unavailable.
    title_font_size (int): The font size of the title text. Defaults to 20.
    subtitle_font_family (str): The font family used for the subtitle text.
        Defaults to "Calibri".
    subtitle_font_size (int): The font size of the subtitle text. Defaults
        to 11.
    spacing (int): The spacing between UI elements in the splash screen.
        Defaults to 10.
    background_color (str): The background color of the splash screen.
        Defaults to "black".
    foreground_color (str): The foreground color, including text and icon
        colors, on the splash screen. Defaults to "white".
    show_progress (bool): Whether a progress indicator should be displayed on
        the splash screen. Defaults to True.
"""
from dataclasses import dataclass, field

from picoui.dimensions import Dimensions
from picoui.specs.widgets import LabelSpec
from picoui.splash.theme import SplashTheme


@dataclass(frozen=True, slots=True)
class SplashScreenConfig:
    """
    Represents configuration options for a splash screen.

    This data class is used to define the appearance and behavior of a
    splash screen, including its title, subtitle, logo, dimensions,
    color scheme, fonts, and additional style options. It leverages frozen
    and slots for immutability and memory efficiency.

    Attributes:
        title (str): The title text displayed on the splash screen.
        subtitle (LabelSpec): Specifications for the subtitle displayed
            on the splash screen, with a default instance.
        logo_path (str | None): The file path to the logo image displayed
            on the splash screen. Defaults to None if no logo is provided.
        style (str): CSS style string applied to the splash screen. Defaults
            to "background-color: black;".
        dimensions (Dimensions): The dimensions of the splash screen, including
            its width and height. The default is 500x400.
        logo_size (Dimensions): The dimensions of the logo displayed on the
            splash screen, including its width and height. The default is 250x150.
        theme (SplashTheme): The theme settings for the splash screen, with
            a default instance.
        title_font_family (tuple[str, ...]): A tuple of font family names
            used for the title text, listed in order of preference.
        title_font_size (int): The font size of the title text. Defaults to 20.
        subtitle_font_family (str): The font family name used for the subtitle
            text. Defaults to "Calibri".
        subtitle_font_size (int): The font size of the subtitle text. Defaults
            to 11.
        spacing (int): The spacing between visual elements in the splash screen.
            Defaults to 10.
        background_color (str): The background color of the splash screen.
            Defaults to "black".
        foreground_color (str): The foreground color of the splash screen,
            including text and other elements. Defaults to "white".
        show_progress (bool): Indicates whether a progress indicator should
            be displayed on the splash screen. Defaults to True.
    """
    title: str
    subtitle: LabelSpec = field(default_factory=LabelSpec)
    logo_path: str | None = None
    style: str = "background-color: black;"

    dimensions: Dimensions = field(
        default_factory=lambda: Dimensions(width=500, height=400)
    )

    logo_size: Dimensions = field(
        default_factory=lambda: Dimensions(width=250, height=150)
    )

    theme: SplashTheme = field(default_factory=SplashTheme)

    title_font_family: tuple[str, ...] = (
        "Myriad Pro",
        "Segoe UI",
        "Arial",
    )
    title_font_size: int = 20
    subtitle_font_family: str = "Calibri"
    subtitle_font_size: int = 11

    spacing: int = 10
    background_color: str = "black"
    foreground_color: str = "white"

    show_progress: bool = True