import os
from pathlib import Path

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger
from matplotlib import pyplot as plt

import movierender.overlays as ovl
from movierender import MovieRenderer, SingleImage
from movierender.overlays.pixel_tools import PixelTools

log = get_logger(name='movielayout')


def make_movie(movie: ConfigMovie, movie_name=None, prefix='', suffix='', folder='.'):
    im = movie.image_file
    movie_name = movie_name if movie_name is not None else os.path.basename(im.image_path)
    filename = prefix + movie_name + suffix + ".mp4"
    base_folder = os.path.abspath(folder)
    path = os.path.join(base_folder, filename)
    if os.path.exists(path):
        log.warning(f'File {filename} already exists in folder {base_folder}.')
        return

    Path(path).touch()
    log.info(f'Making movie {filename} from file {os.path.basename(im.image_path)} in folder {base_folder}.')
    t = PixelTools(im)

    fig = plt.figure(frameon=False, figsize=(5, 5), dpi=150)
    movren = MovieRenderer(image=im,
                           fig=fig,
                           fps=15,
                           show_axis=False,
                           bitrate="10M",
                           fontdict={'size': 12}) + \
             ovl.ScaleBar(um=movie.scalebar, lw=3, xy=t.xy_ratio_to_um(0.70, 0.05), fontdict={'size': 9}) + \
             ovl.Timestamp(xy=t.xy_ratio_to_um(0.02, 0.95), va='center') + \
             SingleImage(ax=fig.gca())
    movren.render(filename=path, test=False)
