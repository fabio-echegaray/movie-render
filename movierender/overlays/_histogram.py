import numpy as np
from fileops.image import MetadataImage

from .overlay import Overlay
from movierender.config import LineProperties


class ImageHistogram(Overlay):
    def __init__(self, line_props=None, **kwargs):
        self._line_props = line_props if line_props is not None else LineProperties(color="magenta")
        super().__init__(**kwargs)

    def plot(self, mdi: MetadataImage, bins=None, ax=None, color=None, **kwargs):
        if ax is None:
            ax = self.ax
        if ax is None:
            raise RuntimeError("No axes found to plot overlay.")

        bins = bins if bins is not None else self._kwargs.get("bins", 10)
        color = color if color is not None else self._line_props.color

        axi = ax.inset_axes(
            (0.5, 0.5, 0.47, 0.47),
            facecolor=color,
            frameon=False
        )

        hist, bins = np.histogram(mdi.image.ravel(), bins=bins)
        axi.hist(bins[:-1], bins, weights=hist, histtype='step', color=color, zorder=10)
        # axi.set_xlabel('intensity', color='white')
        # axi.set_ylabel('pixel count', color='white')
        axi.tick_params(axis='both', colors=color)
