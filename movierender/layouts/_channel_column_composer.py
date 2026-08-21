import itertools
import math
from collections import deque

from fileops.logger import get_logger

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage, plt, gridspec
from movierender.config import ConfigMovie
from movierender.config import TextProperties, LineProperties
from movierender.overlays.pixel_tools import PixelTools
from ._base_composer import BaseLayoutComposer
from ._ch_config import channel_configuration


class LayoutChannelColumnComposer(BaseLayoutComposer):
    log = get_logger(name='LayoutChannelColumnComposer')

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

        # Get graphics parameters from config or use defaults
        sbar_text = movie.scalebar_text or TextProperties(font_size=9)
        sbar_line = movie.scalebar_line or LineProperties(width=3)
        tsmp_text = movie.timestamp or TextProperties()
        ch_text = movie.channel_label or TextProperties(font_size=7)

        if len(movie.channels) > 1:
            fig = plt.figure(figsize=(16, 9), dpi=self.dpi)
            n_channels = len(movie.channels)
            rows = math.ceil(n_channels / self.n_columns)
            gs = gridspec.GridSpec(nrows=rows, ncols=self.n_columns)
            self.log.debug(f"making grid of {rows} rows and {self.n_columns} columns.")

            for i, k in itertools.product(range(rows), range(self.n_columns), ):
                self.ax_lst.append(fig.add_subplot(gs[i, k]))
            fig.subplots_adjust(left=0.01, right=0.99, bottom=.0, top=0.90, wspace=0.01, hspace=0.01)
        else:
            fig = plt.figure(figsize=(5.5, 5.5), dpi=self.dpi)
            self.ax_lst.append(fig.gca())

        # Apply suptitle styling from config
        suptitle_props = movie.suptitle or TextProperties()
        fig.suptitle(self.fig_title, fontname=suptitle_props.font_name,
                     fontsize=suptitle_props.font_size, color=suptitle_props.color)

        # Apply background color from config
        bg_props = movie.background
        if bg_props is not None:
            fig.patch.set_facecolor(bg_props.color)

        self.renderer = MovieRenderer(fig=fig,
                                      config=movie,
                                      fontdict={'size': 12},
                                      **self._renderer_params)

        agg_ch_config = channel_configuration(movie.channel_render_parameters)
        for ax, ch_cfg_ix in zip(self.ax_lst, movie.channel_render_parameters):
            ch_cfg = movie.channel_render_parameters[ch_cfg_ix]
            if movie.scalebar is not None and movie.scalebar > 0:
                self.renderer += ovl.ScaleBar(um=movie.scalebar, lw=sbar_line.width,
                                              xy=t.xy_ratio_to_um(0.80, 0.05),
                                              text_props=sbar_text, line_props=sbar_line,
                                              fontdict={'size': sbar_text.font_size},
                                              ax=ax)
            self.renderer += ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center',
                                           text_props=tsmp_text, ax=ax)
            self.renderer += CompositeRGBImage(
                ax=ax,
                zstack=movie.zstack,
                zstack_fn=movie.zstack_fn,
                channeldict={ch_cfg["name"]: agg_ch_config[ch_cfg["name"]]}
            )
            # Use per-channel font properties if available, otherwise use global channel_label
            ch_label_props = ch_text
            if 'font_name' in ch_cfg or 'font_size' in ch_cfg or 'font_color' in ch_cfg:
                from movierender.config import TextProperties
                ch_label_props = TextProperties(
                    font_name=ch_cfg.get('font_name', ch_text.font_name),
                    font_size=int(ch_cfg.get('font_size', ch_text.font_size)),
                    color=ch_cfg.get('font_color', ch_text.color)
                )
            self.renderer += ovl.Text(f'{ch_cfg["name"]}',
                                      xy=t.xy_ratio_to_um(0.70, 0.95),
                                      text_props=ch_label_props,
                                      fontdict={'size': ch_label_props.font_size, 'color': ch_label_props.color},
                                      ax=ax)

            self._apply_overlays(ax, "channel", ch_cfg_ix)

        self._pending_overlays = deque()
        self._layout_done = True
        super().make_layout()
