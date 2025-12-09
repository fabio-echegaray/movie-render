import copy
import math

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger
from matplotlib import pyplot as plt, gridspec

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage
from movierender.overlays.pixel_tools import PixelTools
from ._base_composer import BaseLayoutComposer


class LayoutColumnComposer(BaseLayoutComposer):
    log = get_logger(name='LayoutColumnComposer')

    def __init__(self,
                 movie: ConfigMovie,
                 columns: int = 2,
                 **kwargs):
        super().__init__(movie, **kwargs)

        self.n_columns = columns

    def make_layout(self):
        movie = self._movie_configuration_params
        t = PixelTools(movie.image_file)

        fig = plt.figure(figsize=(5 * self.n_columns, 5.5), dpi=self.dpi)
        fig.suptitle(self.fig_title)

        if len(movie.channels) > 1:
            n_channels = len(movie.channels)
            rows = math.ceil(n_channels / self.n_columns)
            gs = gridspec.GridSpec(nrows=rows, ncols=self.n_columns)
            self.log.debug(f"making frid of {rows} rows and {self.n_columns} columns.")

            for i in range(n_channels):
                self.ax_lst.append(fig.add_subplot(gs[0, i]))
            fig.subplots_adjust(left=0.125, right=0.9, bottom=0.1, top=0.99, wspace=0.01, hspace=0.01)
        else:
            self.ax_lst.append(fig.gca())

        self.renderer = MovieRenderer(fig=fig,
                                      config=movie,
                                      fontdict={'size': 12})

        for ax, ch_cfg_ix in zip(self.ax_lst, movie.channel_render_parameters):
            ch_cfg = movie.channel_render_parameters[ch_cfg_ix]
            self.renderer += ovl.ScaleBar(um=movie.scalebar, lw=3,
                                          xy=t.xy_ratio_to_um(0.80, 0.05),
                                          fontdict={'size': 9},
                                          ax=ax)
            self.renderer += ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center', ax=ax)
            self.renderer += CompositeRGBImage(ax=ax,
                                               zstack=movie.zstack_fn,
                                               channeldict={
                                                   ch_cfg['name']: {
                                                       'id':        ch_cfg_ix,
                                                       'color':     ch_cfg['color'][1:] if (
                                                               isinstance(ch_cfg['color'], tuple) and
                                                               len(ch_cfg['color']) > 3
                                                       ) else ch_cfg['color'],
                                                       'rescale':   True,
                                                       'intensity': 1.0
                                                   },
                                               })
            self.renderer += ovl.Text(f'{ch_cfg["name"]}',
                                      xy=t.xy_ratio_to_um(0.70, 0.95),
                                      fontdict={'size': 7, 'color': 'white'}, ax=ax)

    def add_overlay(self, overlay: ovl.Overlay):
        for ax in self.ax_lst:
            _o = copy.deepcopy(overlay)
            _o.ax = ax
            self.renderer += _o
