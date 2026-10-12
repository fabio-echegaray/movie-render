import matplotlib.ticker as ticker
import numpy as np
from fileops import get_logger
from fileops.image import MetadataImage

from movierender.config import LineProperties
from .overlay import Overlay


class ImageHistogram(Overlay):
    log = get_logger("ImageHistogram")

    def __init__(self, line_props=None, **kwargs):
        self._line_props = line_props if line_props is not None else LineProperties(color="gray")
        super().__init__(**kwargs)

    def plot(self, mdi: MetadataImage, bins=None, ax=None, color=None, channel_params=None, **kwargs):
        if ax is None:
            ax = self.ax
        if ax is None:
            raise RuntimeError("No axes found to plot overlay.")

        bins = bins if bins is not None else self._kwargs.get("bins", 10)
        color = color if color is not None else self._line_props.color

        axi = ax.inset_axes(
            (0.0, 0.3, 0.98, 0.1),
            facecolor=color,
            frameon=False
        )

        if isinstance(mdi, np.ndarray):
            data = mdi
            if data.ndim == 3:
                data = data.mean(axis=-1)
        else:
            data = mdi.image
        hist, bins = np.histogram(data.ravel(), bins=bins)
        axi.hist(bins[:-1], bins, weights=hist, histtype='bar', color=color, log=False, lw=0.1, zorder=1000)
        # axi.set_xlabel('intensity', color='white')
        # axi.set_ylabel('pixel count', color='white')
        axi.set_yticks([])
        axi.tick_params(axis='both', colors=color, labelsize=3)
        axi.xaxis.set_major_formatter(ticker.EngFormatter())
        # axi.set_xscale('log')

        if channel_params:
            self.log.debug(f"channel params: {channel_params}")
            if "rescale_min" in channel_params:
                self.log.debug(f"rescale_min in channel_params")
                axi.axvline(channel_params["rescale_min"], color="r", linestyle="-", linewidth=1, zorder=1000)
            if "rescale_max" in channel_params:
                self.log.debug(f"rescale_max in channel_params")
                axi.axvline(channel_params["rescale_max"], color="g", linestyle="-", linewidth=1, zorder=1000)
