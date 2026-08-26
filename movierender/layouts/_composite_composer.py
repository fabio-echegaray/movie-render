from fileops.logger import get_logger

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage, plt
from movierender.config import ConfigMovie
from movierender.config import TextProperties, LineProperties
from movierender.config._cfg_graphics import resolve_text_color
from movierender.overlays.pixel_tools import PixelTools
from ._base_composer import BaseLayoutComposer
from ._ch_config import channel_configuration


class LayoutCompositeComposer(BaseLayoutComposer):
    log = get_logger(name='LayoutColumnComposer')

    def __init__(self,
                 movie: ConfigMovie,
                 **kwargs):
        super().__init__(movie, **kwargs)

    def make_layout(self):
        if self._layout_done:
            return

        movie = self._movie_configuration_params
        t = PixelTools(movie.image_file)

        # Get graphics parameters from config or use defaults
        sbar_text = movie.scalebar_text or TextProperties(font_size=9)
        sbar_line = movie.scalebar_line or LineProperties(width=3)
        tsmp_text = movie.timestamp or TextProperties()

        fig = plt.figure(figsize=(5.5, 5.5), dpi=self.dpi)
        # Apply suptitle styling from config
        suptitle_props = movie.suptitle or TextProperties()
        bg_color = movie.background.color if movie.background is not None else 'black'
        fig.suptitle(self.fig_title, fontname=suptitle_props.font_name,
                     fontsize=suptitle_props.font_size,
                     fontweight=suptitle_props.font_weight,
                     color=resolve_text_color(suptitle_props.color, bg_color))

        # Apply background color from config
        bg_props = movie.background
        if bg_props is not None:
            fig.patch.set_facecolor(bg_props.color)

        # only one axes is rendered
        ax = fig.gca()
        self.ax_lst.append(ax)

        ch_cfg = channel_configuration(movie.channel_render_parameters)
        self.renderer = MovieRenderer(fig=fig,
                                      config=movie,
                                      fontdict={'size': 12},
                                      **self._renderer_params)
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
            channeldict=ch_cfg
        )

        self._layout_done = True
        super().make_layout()
