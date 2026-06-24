from fileops.logger import get_logger

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage, plt
from movierender.config import ConfigMovie
from movierender.overlays.pixel_tools import PixelTools
from ._base_composer import BaseLayoutComposer


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

        fig = plt.figure(figsize=(5.5, 5.5), dpi=self.dpi)
        fig.suptitle(self.fig_title)

        # only one axes is rendered
        ax = fig.gca()
        self.ax_lst.append(ax)

        self.renderer = MovieRenderer(fig=fig,
                                      config=movie,
                                      fontdict={'size': 12},
                                      **self._renderer_params)

        self.renderer += ovl.ScaleBar(um=movie.scalebar, lw=3,
                                      xy=t.xy_ratio_to_um(0.80, 0.05),
                                      fontdict={'size': 9},
                                      ax=ax)
        self.renderer += ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center', ax=ax)
        self.renderer += CompositeRGBImage(
            ax=ax,
            zstack=movie.zstack,
            zstack_fn=movie.zstack_fn,
            channeldict={
                ch_cfg['name']: {
                    'id':          cix,
                    'color':       ch_cfg['color'][1:] if (
                            isinstance(ch_cfg['color'], tuple) and
                            len(ch_cfg['color']) > 3
                    ) else ch_cfg['color'],
                    'gamma_value': float(ch_cfg['gamma_value']) if 'gamma_value' in ch_cfg else 1.0,
                    'gamma_gain':  float(ch_cfg['gamma_gain']) if 'gamma_gain' in ch_cfg else 1.0,
                    'rescale':     ch_cfg['rescale'].lower() in ['true', 'yes'] if 'rescale' in ch_cfg else True,
                    'rescale_min': float(ch_cfg['rescale_min']) if 'rescale_min' in ch_cfg else None,
                    'rescale_max': float(ch_cfg['rescale_max']) if 'rescale_max' in ch_cfg else None,
                    'intensity':   float(ch_cfg['intensity']) if 'intensity' in ch_cfg else 1.0
                } for cix, ch_cfg in movie.channel_render_parameters.items()})

        self._layout_done = True
        super().make_layout()
