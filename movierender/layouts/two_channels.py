import os
from pathlib import Path

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger
from matplotlib import pyplot as plt, gridspec

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage
from movierender.overlays.pixel_tools import PixelTools

log = get_logger(name='movielayout')

green = [0, 1, 0]
red = [1, 0, 0]


def make_movie(movie: ConfigMovie, id_red=0, id_green=1,
               prefix='', name='', suffix='', folder='.', overwrite=False,
               fig_title=''):
    im = movie.image_file
    assert len(im.channels) >= 2, 'Image series contains less than two channels.'
    fname = name if len(name) > 0 else os.path.basename(im.image_path)
    filename = prefix + fname + suffix + ".twoch.mp4"
    base_folder = os.path.abspath(folder)
    path = os.path.join(base_folder, filename)
    if os.path.exists(path):
        if not overwrite:
            log.warning(f'File {filename} already exists in folder {base_folder}.')
            return

    Path(path).touch()
    log.info(f'Making movie {filename} from file {os.path.basename(im.image_path)} in folder {base_folder}.')
    t = PixelTools(im)

    ar = float(im.height) / float(im.width)
    log.debug(f'aspect ratio={ar}.')

    fig = plt.figure(figsize=(10, 5.5), dpi=150)
    gs = gridspec.GridSpec(nrows=1, ncols=2)
    fig.suptitle(fig_title)

    ax_ch1 = fig.add_subplot(gs[0, 0])
    ax_ch2 = fig.add_subplot(gs[0, 1])
    fig.subplots_adjust(left=0.125, right=0.9, bottom=0.1, top=0.99, wspace=0.01, hspace=0.01)
    movren = MovieRenderer(fig=fig,
                           config=movie,
                           fontdict={'size': 12}) + \
             ovl.ScaleBar(um=movie.scalebar, lw=3, xy=t.xy_ratio_to_um(0.80, 0.05), fontdict={'size': 9}, ax=ax_ch1) + \
             ovl.ScaleBar(um=movie.scalebar, lw=3, xy=t.xy_ratio_to_um(0.80, 0.05), fontdict={'size': 9}, ax=ax_ch2) + \
             ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center', ax=ax_ch1) + \
             ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center', ax=ax_ch2) + \
             CompositeRGBImage(ax=ax_ch1,
                               zstack=movie.zstack_fn,
                               channeldict={
                                   'Channel1': {
                                       'id':        id_red,
                                       'color':     red,
                                       'rescale':   True,
                                       'intensity': 1.0
                                   },
                               }) + \
             CompositeRGBImage(ax=ax_ch2,
                               zstack=movie.zstack_fn,
                               channeldict={
                                   'Channel2': {
                                       'id':        id_green,
                                       'color':     green,
                                       'rescale':   True,
                                       'intensity': 1.0
                                   },
                               })
    movren.render(filename=path)
