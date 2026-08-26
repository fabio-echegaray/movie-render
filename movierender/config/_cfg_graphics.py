"""Graphics parameter classes for movie and panel rendering.

Defines composable, general-purpose property classes that describe visual
characteristics of graphic elements. Each class represents a style group
(text, line, background) and can be applied to any overlay or built-in
element that uses those properties.

Property classes are designed to be independent of specific overlays.
Overlays accept whichever properties apply to them via their constructors,
and the layout code passes the appropriate instances from ConfigMovie/ConfigPanel.

Usage in overlays:
    class Text(Overlay):
        def __init__(self, text, text_props: TextProperties = None, **kwargs):
            self._text_props = text_props or TextProperties()
            ...

Usage in layouts:
    gfx_text = movie.text or TextProperties(font_size=7)
    self.renderer += ovl.Text(..., text_props=gfx_text)
"""

from typing import NamedTuple


class TextProperties(NamedTuple):
    """Font and color properties for text elements.

    Applies to: ScaleBar label, Timestamp, Text overlay, Treatment labels,
    channel labels, figure suptitle.

    Attributes:
        font_name: Font family name (e.g. 'Arial', 'Helvetica').
        font_size: Font size in points.
        color: Text color as CSS name, RGB tuple, or hex string.
               ``None`` means "auto-pick black or white to contrast with
               the background" (resolved at render time).
    """
    font_name: str = 'Arial'
    font_size: int = 12
    color: str | None = None


class LineProperties(NamedTuple):
    """Color and width properties for line elements.

    Applies to: ScaleBar line, histogram bars, arrow shafts,
    timeseries traces, ROI outlines.

    Attributes:
        color: Line color as CSS name, RGB tuple, or hex string.
        width: Line width in points.
    """
    color: str = 'white'
    width: float = 1.0


class BackgroundProperties(NamedTuple):
    """Background fill properties.

    Applies to: Figure background, axes background, histogram inset.

    Attributes:
        color: Background color as CSS name, RGB tuple, or hex string.
    """
    color: str = 'black'


_TEXT_DEFAULTS = TextProperties()
_LINE_DEFAULTS = LineProperties()
_BACKGROUND_DEFAULTS = BackgroundProperties()


def contrast_color(bg_color: str) -> str:
    """Return 'black' or 'white' to contrast with the given background color.

    Uses the ITU-R BT.601 luminance formula to decide whether the
    background is light or dark.
    """
    from matplotlib.colors import to_rgb
    r, g, b = to_rgb(bg_color)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return 'black' if luminance > 0.5 else 'white'


def resolve_text_color(text_color: str | None, bg_color: str | None) -> str:
    """Resolve a text color, auto-picking contrast color when *text_color* is ``None``."""
    if text_color is not None:
        return text_color
    return contrast_color(bg_color or 'black')


# ---------------------------------------------------------------------------
# Parsing helpers — used by header readers to convert config keys → property
# instances. Shared between movie and panel readers.
# ---------------------------------------------------------------------------

def _parse_text_props(cfg_section, prefix) -> TextProperties:
    """Parse TextProperties from a config section using dot-separated keys.

    Looks for keys like ``{prefix}.font_name``, ``{prefix}.font_size``,
    ``{prefix}.color``.  Missing keys fall back to TextProperties defaults.

    Args:
        cfg_section: A configparser section proxy (e.g. ``cfg["MOVIE"]``).
        prefix: Key prefix (e.g. ``"scalebar"``, ``"timestamp"``).

    Returns:
        A TextProperties instance.
    """
    font_name = cfg_section.get(f"{prefix}.font_name", _TEXT_DEFAULTS.font_name)
    font_size = cfg_section.get(f"{prefix}.font_size", None)
    color = cfg_section.get(f"{prefix}.color", _TEXT_DEFAULTS.color)

    return TextProperties(
        font_name=font_name if font_name else _TEXT_DEFAULTS.font_name,
        font_size=int(font_size) if font_size else _TEXT_DEFAULTS.font_size,
        color=color if color else _TEXT_DEFAULTS.color,
    )


def _parse_line_props(cfg_section, prefix) -> LineProperties:
    """Parse LineProperties from a config section using dot-separated keys.

    Looks for keys like ``{prefix}.line_color``, ``{prefix}.line_width``.

    Args:
        cfg_section: A configparser section proxy.
        prefix: Key prefix (e.g. ``"scalebar"``).

    Returns:
        A LineProperties instance.
    """
    color = cfg_section.get(f"{prefix}.line_color", None)
    width = cfg_section.get(f"{prefix}.line_width", None)

    return LineProperties(
        color=color if color else _LINE_DEFAULTS.color,
        width=float(width) if width else _LINE_DEFAULTS.width,
    )


def _parse_background_props(cfg_section) -> BackgroundProperties:
    """Parse BackgroundProperties from a config section.

    Looks for key ``background.color``.

    Args:
        cfg_section: A configparser section proxy.

    Returns:
        A BackgroundProperties instance.
    """
    color = cfg_section.get("background.color", None)

    return BackgroundProperties(
        color=color if color else _BACKGROUND_DEFAULTS.color,
    )


def _parse_overlay_text_props(cfg_section) -> TextProperties:
    """Parse TextProperties from an overlay section (no prefix).

    Looks for keys ``font_name``, ``font_size``, ``font_color``.

    Args:
        cfg_section: A configparser section proxy for an OVERLAY section.

    Returns:
        A TextProperties instance.
    """
    font_name = cfg_section.get("font_name", _TEXT_DEFAULTS.font_name)
    font_size = cfg_section.get("font_size", None)
    color = cfg_section.get("font_color", _TEXT_DEFAULTS.color)

    return TextProperties(
        font_name=font_name if font_name else _TEXT_DEFAULTS.font_name,
        font_size=int(font_size) if font_size else _TEXT_DEFAULTS.font_size,
        color=color if color else _TEXT_DEFAULTS.color,
    )


def _parse_overlay_line_props(cfg_section) -> LineProperties:
    """Parse LineProperties from an overlay section (no prefix).

    Looks for keys ``color``, ``line_width``.

    Args:
        cfg_section: A configparser section proxy for an OVERLAY section.

    Returns:
        A LineProperties instance.
    """
    color = cfg_section.get("color", None)
    width = cfg_section.get("line_width", None)

    return LineProperties(
        color=color if color else _LINE_DEFAULTS.color,
        width=float(width) if width else _LINE_DEFAULTS.width,
    )
