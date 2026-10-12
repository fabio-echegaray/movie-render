"""Colour application for depth-coded z-projections.

Depth-coded rendering is composed of two parts working in a complementary manner:

* **Data** (FileOps): ``z_volume`` assembles the z-stack of one channel into
  a volume, and ``depth_field`` turns it into the per-pixel position of peak
  intensity (0 = bottom, 1 = top).  Neither of these is a *projection type*:
  max/min/mean are reducers over z, whereas depth is a derived measurement.
* **Presentation** (this module, MovieRender): mapping that depth data to
  colours through a colormap, scaled by the pixel's normalised max-intensity
  so that dark regions stay black.
"""

import numpy as np
from matplotlib import pyplot as plt

from fileops.image.ops import depth_field, z_volume

# Default colormap for depth-coding.  'jet' is deliberately avoided: it is not
# perceptually uniform (lightness jumps and dark bands that read as structure),
# so colours can easily be mistaken for intensity levels.  'plasma' is
# perceptually uniform with a mostly monotonic lightness ramp, which is the
# right encoding for a linear bottom→top depth axis.
DEFAULT_DEPTH_CMAP = 'plasma'

# Depth-coded rendering is signalled by these names in the configuration.
# They are not projection types (see module docstring), so MovieRender
# intercepts them before FileOps' projection machinery is reached.
_DEPTH_NAMES = frozenset({'depth', 'code'})


def is_depth_projection(proj) -> bool:
    """Whether a configured projection requests depth-coded rendering.

    ``'depth'``/``'code'`` (optionally prefixed with ``'all-'``) are a
    MovieRender rendering convention and are not part of
    :class:`fileops.image.ops.ZProjection`; this is the one place that parses
    them.
    """
    if not isinstance(proj, str):
        return False
    proj = proj.lower()
    if proj.startswith('all-'):
        proj = proj.split('-', 1)[1]
    return proj in _DEPTH_NAMES


def normalized_intensity(im_max: np.ndarray) -> np.ndarray:
    """Normalise a max-intensity map to [0, 1]."""
    vmin, vmax = np.min(im_max), np.max(im_max)
    if vmax > vmin:
        return (im_max - vmin) / (vmax - vmin)
    return np.zeros_like(im_max)


def depth_cmap(depth_field: np.ndarray, intensity: np.ndarray,
               cmap_name: str = DEFAULT_DEPTH_CMAP) -> np.ndarray:
    """Colour a depth field into an RGB array.

    ``depth_field`` is the ``(H, W)`` normalised argmax-z field (0 = bottom,
    1 = top) produced by FileOps' depth projection; ``intensity`` is the
    matching ``(H, W)`` normalised max-intensity used as brightness.  Returns
    an ``(H, W, 3)`` RGB array of floats in [0, 1].
    """
    try:
        cmap = plt.get_cmap(cmap_name)
    except ValueError:
        raise ValueError(
            f"Unknown colormap name for depth-coding: {cmap_name!r}. "
            "Use any valid matplotlib colormap (e.g. 'plasma', 'viridis', 'turbo')."
        ) from None
    rgb = cmap(depth_field)[..., :3]
    return rgb * intensity[..., np.newaxis]


def z_depth_rgb(imf, frame, channel, z_subset=None,
                cmap_name: str = DEFAULT_DEPTH_CMAP) -> np.ndarray:
    """Coloured depth projection of one channel: ``(H, W, 3)`` RGB floats.

    Assembles the channel's z-stack into a volume (FileOps ``z_volume``),
    derives the depth data (position of peak intensity) and the per-pixel
    brightness from it, then maps it through the colormap.
    """
    vol = z_volume(imf, frame=frame, channel=channel, z_subset=z_subset)
    depth = depth_field(vol)
    intensity = normalized_intensity(np.max(vol, axis=0))
    return depth_cmap(depth, intensity, cmap_name)