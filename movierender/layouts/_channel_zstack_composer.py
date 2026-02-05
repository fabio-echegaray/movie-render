import itertools
import math
from collections import deque

from fileops.logger import get_logger

import movierender.overlays as ovl
from movierender import MovieRenderer, plt, gridspec
from movierender.config import ConfigMovie
from movierender.overlays.pixel_tools import PixelTools
from movierender.plugins.overlay import OverlayPlugin
from movierender.render.pipelines import NullImage, CompositeRGBImage
from ._base_composer import BaseLayoutComposer


class LayoutZStackColumnComposer(BaseLayoutComposer):
    log = get_logger(name='LayoutZStackColumnComposer')

    def __init__(self,
                 movie: ConfigMovie,
                 n_columns: int = 2,
                 **kwargs):
        super().__init__(movie, **kwargs)

        self.n_columns = n_columns

    def make_layout(self):
        if self._layout_done:
            return

        movie = self._movie_configuration_params
        t = PixelTools(movie.image_file)

        imf = movie.image_file
        z_ax_dct = dict()
        if imf.n_zstacks > 1:
            rows = math.ceil(imf.n_zstacks / self.n_columns)
            fig = plt.figure(figsize=(14, 9), dpi=self.dpi)

            gs = gridspec.GridSpec(nrows=rows, ncols=self.n_columns)
            self.log.debug(f"making grid of {rows} rows and {self.n_columns} columns.")

            for j, (i, k) in enumerate(itertools.product(range(rows), range(self.n_columns), )):
                z_ax_dct[j] = fig.add_subplot(gs[i, k])
                self.ax_lst.append(z_ax_dct[j])
            fig.subplots_adjust(left=0.125, right=0.9, bottom=0.01, top=0.95, wspace=0.01, hspace=0.01)
        else:
            fig = plt.figure(figsize=(5.5, 5.5), dpi=self.dpi)
            z_ax_dct[0] = fig.gca()
            self.ax_lst.append(fig.gca())

        fig.suptitle(self.fig_title)
        self.renderer = MovieRenderer(fig=fig,
                                      config=movie,
                                      fontdict={'size': 12},
                                      **self._renderer_params)

        ch_indexes = sorted(movie.channel_render_parameters.keys())
        ch_cfg = movie.channel_render_parameters[ch_indexes[0]]  # we take the first channel regardless of their number
        for ax, z_ix in zip(self.ax_lst, imf.zstacks):
            self.renderer += ovl.ScaleBar(um=movie.scalebar, lw=3,
                                          xy=t.xy_ratio_to_um(0.80, 0.05),
                                          fontdict={'size': 9},
                                          ax=ax)
            self.renderer += ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center', ax=ax)
            self.renderer += CompositeRGBImage(ax=ax,
                                               zstack=z_ix,
                                               channeldict={
                                                   ch_cfg['name']: {
                                                       'id':        ch_indexes[0],
                                                       'color':     ch_cfg['color'][1:] if (
                                                               isinstance(ch_cfg['color'], tuple) and
                                                               len(ch_cfg['color']) > 3
                                                       ) else ch_cfg['color'],
                                                       'rescale':   True,
                                                       'intensity': 1.0
                                                   },
                                               })
            self.renderer += ovl.Text(f'z{z_ix:02d}',
                                      xy=t.xy_ratio_to_um(0.70, 0.95),
                                      fontdict={'size': 7, 'color': 'white'}, ax=ax)

            # consume overlays previously added
            for ovrl in self._pending_overlays:
                if isinstance(ovrl, OverlayPlugin):
                    ovrl = ovrl.overlay
                    ovrl.ax = ax
                if hasattr(ovrl, "z"):
                    if getattr(ovrl, "z") == z_ix:
                        self.renderer += ovrl
                else:
                    self.renderer += ovrl

        for zk in z_ax_dct.keys():
            if zk > imf.n_zstacks - 1:
                self.renderer += NullImage(ax=z_ax_dct[zk])

        self._pending_overlays = deque()
        self._layout_done = True
        super().make_layout()
