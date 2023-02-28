"""
This script renders a movie of a timeseries comprised of z-projection from a z-stack; all this specified from
a configuration file. If there is a definition for ROIs, then these will be overlaid on top of the movie.
"""
import os
from pathlib import Path

import javabridge
import matplotlib.pyplot as plt

import movierender.overlays as ovl
from fileops.export import ExportConfig, read_config
from fileops.logger import get_logger
from fileops.movielayouts import scalebar
from fileops.pathutils import ensure_dir
from movierender import MovieRenderer, PixelTools, CompositeRGBImage

log = get_logger(name='export')

red = [1, 0, 0]
green = [0, 1, 0]
blue = [0, 0, 1]


def make_movie(cfg: ExportConfig):
    imf = cfg.image_file
    folder = cfg.path

    fname = "max_projection_with_roi.mp4"
    path = ensure_dir(folder) / fname
    if os.path.exists(path):
        log.warning(f'File {fname} already exists in folder {folder}.')
        return

    log.info(f'Making movie {fname} in folder {folder}')
    t = PixelTools(imf)

    mag = imf.magnification if imf.magnification is not None else 0

    fig = plt.figure(frameon=False, figsize=(10, 10), dpi=150)
    ax = fig.gca()

    movren = MovieRenderer(fig=fig,
                           image=imf,
                           fps=10,
                           bitrate="6M",
                           fontdict={'size': 12}) + \
             ovl.ScaleBar(ax=ax, um=scalebar[mag], lw=3, xy=t.xy_ratio_to_um(0.80, 0.05), fontdict={'size': 9}) + \
             ovl.Timestamp(ax=ax, xy=t.xy_ratio_to_um(0.02, 0.95), va='center') + \
             ovl.ImagejROI([cfg.roi]) + \
             CompositeRGBImage(ax=ax, zstack="all-max",
                               channeldict={
                                   'Channel0': {
                                       'id':        0,
                                       'color':     red,
                                       'rescale':   True,
                                       'intensity': 0.6
                                   },
                                   'Channel1': {
                                       'id':        1,
                                       'color':     green,
                                       'rescale':   True,
                                       'intensity': 0.6
                                   },
                               })
    log.info(f"saving movie to {path}")
    movren.render(filename=str(path))


if __name__ == "__main__":
    cfg_paths = [
        Path("/home/lab/Documents/Fabio/Blender/fig-1a/export_definition.cfg"),
        Path("/home/lab/Documents/Fabio/Blender/fig-1b/export_definition.cfg"),
        Path("/home/lab/Documents/Fabio/Blender/fig-1c/export_definition.cfg"),
        Path("/home/lab/Documents/Fabio/Blender/fig-1d/export_definition.cfg"),
        Path("/home/lab/Documents/Fabio/Blender/fig-1e/export_definition.cfg"),
        Path("/home/lab/Documents/Fabio/Blender/fig-1f/export_definition.cfg"),
    ]

    for cfg_path in cfg_paths:
        make_movie(read_config(cfg_path))

    javabridge.kill_vm()
