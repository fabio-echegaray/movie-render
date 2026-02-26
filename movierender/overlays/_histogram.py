import numpy as np
from fileops.image import MetadataImage

from .overlay import Overlay


class ImageHistogram(Overlay):
    def plot(self, mdi: MetadataImage, bins=None, ax=None, color=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        bins = bins if bins is not None else self._kwargs.get("bins", 10)
        color = color if color is not None else self._kwargs.get("color", "magenta")

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
