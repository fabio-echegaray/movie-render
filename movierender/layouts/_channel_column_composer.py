import itertools
import math

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage, plt, gridspec
from movierender.overlays.pixel_tools import PixelTools
from ._base_composer import BaseLayoutComposer


class LayoutChannelColumnComposer(BaseLayoutComposer):
    log = get_logger(name='LayoutChannelColumnComposer')

    def __init__(self,
                 movie: ConfigMovie,
                 columns: int = 2,
                 **kwargs):
        super().__init__(movie, **kwargs)

        self.n_columns = columns

    def make_layout(self):
        movie = self._movie_configuration_params
        t = PixelTools(movie.image_file)

        if len(movie.channels) > 1:
            fig = plt.figure(figsize=(14, 9), dpi=self.dpi)
            n_channels = len(movie.channels)
            rows = math.ceil(n_channels / self.n_columns)
            gs = gridspec.GridSpec(nrows=rows, ncols=self.n_columns)
            self.log.debug(f"making grid of {rows} rows and {self.n_columns} columns.")

            for i, k in itertools.product(range(rows), range(self.n_columns), ):
                self.ax_lst.append(fig.add_subplot(gs[i, k]))
            fig.subplots_adjust(left=0.125, right=0.9, bottom=0.01, top=0.95, wspace=0.01, hspace=0.01)
        else:
            fig = plt.figure(figsize=(5.5, 5.5), dpi=self.dpi)
            self.ax_lst.append(fig.gca())

        fig.suptitle(self.fig_title)

        self.renderer = MovieRenderer(fig=fig,
                                      config=movie,
                                      fontdict={'size': 12},
                                      **self._renderer_params)

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
