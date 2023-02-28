from typing import List

from matplotlib import patches
from roifile import ImagejRoi

from .overlay import Overlay


class ImagejROI(Overlay):
    def __init__(self, roi_list: List[ImagejRoi] = None, **kwargs):
        # assert roi_list is not None, "Need ROIs to render on axes."
        self.roi_lst = roi_list
        super().__init__(**kwargs)

    def plot(self, ax=None, xy=(0, 0), fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        # scale = self._renderer.image.pix_per_um
        scale = self._renderer.image.um_per_pix
        for roi in self.roi_lst:
            w = abs(roi.right - roi.left) * scale
            h = abs(roi.top - roi.bottom) * scale
            r, c = (self._renderer.image.height - roi.bottom) * scale, roi.left * scale
            # ax.text(c + 0.5 * w, r + 1.2 * h, s, ha="center", va="center", c="w", size=5)

            # color = self._style[s]['color'] if self._style is not None and 'color' in self._style[s] else None
            # color = color if color is not None else 'w'
            color = 'yellow'

            rect = patches.Rectangle((c, r), w, h, linewidth=1, edgecolor=color, facecolor='none', zorder=100)
            ax.add_patch(rect)
