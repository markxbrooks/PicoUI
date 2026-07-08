from dataclasses import dataclass, field

from picoui.dimensions import Dimensions
from picoui.splash.theme import SplashTheme


@dataclass(frozen=True, slots=True)
class SplashScreenConfig:
    title: str
    subtitle: str = ""
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