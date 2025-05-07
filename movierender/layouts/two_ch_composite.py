import os
from pathlib import Path

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger
from matplotlib.figure import Figure

import movierender.overlays as ovl
from movierender import MovieRenderer, CompositeRGBImage
from movierender.overlays.pixel_tools import PixelTools

log = get_logger(name='movielayout')

alexa_488 = [.29, 1., 0]
alexa_594 = [1., .61, 0]
alexa_647 = [.83, .28, .28]
hoechst_33342 = [0, .57, 1.]
red = [1, 0, 0]
green = [0, 1, 0]
blue = [0, 0, 1]


def make_movie(movie: ConfigMovie, id_red=0, id_green=1, zstack='all-max',
               prefix='', name='', suffix='', folder='.', overwrite=False,
               fig_title='', fps=10):
    im = movie.image_file
    assert len(im.channels) >= 2, 'Image series contains less than two channels.'
    fname = name if len(name) > 0 else os.path.basename(im.image_path)
    filename = prefix + fname + suffix + ".twochcmp.mp4"
    base_folder = os.path.abspath(folder)
    path = os.path.join(base_folder, filename)
    if os.path.exists(path):
        log.warning(f'File {filename} already exists in folder {base_folder}.')
        if not overwrite:
            return

    Path(path).touch()
    log.info(f'Making movie {filename} from file {os.path.basename(im.image_path)} in folder {base_folder}.')
    t = PixelTools(im)

    ar = float(im.height) / float(im.width)
    log.info(f'aspect ratio={ar}.')

    fig = Figure(frameon=False, figsize=(10, 10), dpi=150)
    ax = fig.gca()
    fig.suptitle(fig_title)

    movren = MovieRenderer(fig=fig,
                           image=im,
                           fps=fps,
                           bitrate="15M",
                           fontdict={'size': 12}) + \
             ovl.ScaleBar(um=movie.scalebar, lw=3, xy=t.xy_ratio_to_um(0.10, 0.05), fontdict={'size': 9}, ax=ax) + \
             ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center', ax=ax) + \
             CompositeRGBImage(ax=ax,
                               zstack=zstack,
                               channeldict={
                                   'H2-RFP':  {
                                       'id':        id_red,
                                       'color':     red,
                                       'rescale':   True,
                                       'intensity': 1
                                   },
                                   'Sqh-GFP': {
                                       'id':        id_green,
                                       'color':     alexa_488,
                                       'rescale':   True,
                                       'intensity': 1
                                   },
                               })
    movren.render(filename=path)
