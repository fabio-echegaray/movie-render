from typing import List

from matplotlib import patches
from roifile import ImagejRoi

from movierender.plugins.overlay import OverlayPlugin
from .overlay import Overlay, get_kwargs


class ImagejROI(Overlay):
    def __init__(self, roi_list: List[ImagejRoi] = None, **kwargs):
        if not isinstance(roi_list, (list, tuple)):
            roi_list = [roi_list]
        if not all(r is not None for r in roi_list):
            raise ValueError("Need ROIs to render on axes.")
        self.roi_list = roi_list
        self._kwargs = kwargs
        super().__init__(**kwargs)

    def plot(self, ax=None, frame=None, xy=(0, 0), fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        if ax is None:
            raise RuntimeError("No axes found to plot overlay.")

        fr = frame
        if fr is None and self._renderer is not None:
            fr = self._renderer.frame

        def_values = get_kwargs([kwargs, self._kwargs],
                                keys_and_default_values=dict(
                                    um_per_pix=self._renderer.image.um_per_pix if self._renderer is not None else 1,
                                    color='yellow'
                                ))

        scale, color = def_values
        for roi in self.roi_list:
            t_pos = getattr(roi, 't_position', None)
            if t_pos is not None and t_pos != fr:
                continue
            w = abs(roi.right - roi.left) * scale
            h = abs(roi.top - roi.bottom) * scale
            r, c = roi.top * scale, roi.left * scale

            rect = patches.Rectangle((c, r), w, h, linewidth=0.1, edgecolor=color, facecolor='none', zorder=100)
            ax.add_patch(rect)


class ImagejROIOverlayPlugin(OverlayPlugin):
    """Overlay-plugin wrapper around :class:`ImagejROI` so ROIs can be listed
    in a PANEL/MOVIE ``overlays`` parameter (matched by section ``id`` or
    header)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._clz = ImagejROI
