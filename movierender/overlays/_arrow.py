import matplotlib.colors as mcolors
import numpy as np

from movierender.plugins.overlay import OverlayPlugin
from .overlay import Overlay, get_kwargs


class ArrowOverlayPlugin(OverlayPlugin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clz = Arrow


class Arrow(Overlay):
    def __init__(self, x, y, length=1, angle=0, overlay_id="default_arrow", c="yellow", style_dict=None, frame=None, **kwargs):
        self.overlay_id = overlay_id
        self._xy = (x, y)
        self._length = length
        self._angle = angle
        self._angle_rad = np.deg2rad(angle)
        self._c = mcolors.to_rgb(c)
        self._style = style_dict
        kwargs.update({"frame": frame})

        super().__init__(**kwargs)

    def plot(self, ax=None, legend=False, lw=2, tail_length=10, frame=None, z=None, **kwargs):
        if ax is None:
            ax = self.ax
        if ax is None:
            raise RuntimeError("No axes found to plot overlay.")

        def_values = get_kwargs([kwargs, self._kwargs],
                                keys_and_default_values=dict(
                                    frame=None,
                                    z=None,
                                ))
        fr, _z = def_values

        if fr is not None and (self._renderer is not None or frame is not None):
            if self._renderer is not None and fr != self._renderer.frame:
                return
            elif frame is not None and fr != frame:
                return
        if z is not None and _z != z:
            return

        length = self._length
        # the base of the arrow is what we need to calculate
        x, y = self._xy
        xb, yb = x + length * np.cos(self._angle_rad), y + length * np.sin(self._angle_rad)
        ax.annotate("", xytext=(xb, yb), xy=(x, y),
                    arrowprops=dict(arrowstyle="-|>", fc=self._c, ec=self._c, shrinkA=0), )
