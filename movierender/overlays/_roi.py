from typing import List

from matplotlib import patches
from roifile import ImagejRoi

from .overlay import Overlay


class ImagejROI(Overlay):
    def __init__(self, roi_list: List[ImagejRoi] = None, **kwargs):
        if not all(r is not None for r in roi_list):
            raise ValueError("Need ROIs to render on axes.")
        self.roi_list = roi_list
        self._kwargs = kwargs
        super().__init__(**kwargs)

    def plot(self, ax=None, xy=(0, 0), fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        fr = self._renderer.frame if self._renderer is not None else max(r.t_position for r in self.roi_list)

        # scale = self._renderer.image.pix_per_um
        scale = self._renderer.image.um_per_pix
        for roi in self.roi_list:
            if roi.t_position != fr:
                continue
            w = abs(roi.right - roi.left) * scale
            h = abs(roi.top - roi.bottom) * scale
            # r, c = (self._renderer.image.height - roi.bottom) * scale, roi.left * scale
            r, c = roi.top * scale, roi.left * scale
            # ax.text(c + 0.5 * w, r + 1.2 * h, s, ha="center", va="center", c="w", size=5)

            # color = self._style[s]['color'] if self._style is not None and 'color' in self._style[s] else None
            # color = color if color is not None else 'w'
            color = 'yellow'

            rect = patches.Rectangle((c, r), w, h, linewidth=1, edgecolor=color, facecolor='none', zorder=100)
            ax.add_patch(rect)
