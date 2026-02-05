import os
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

from movierender.config import ConfigMovie
from movierender.layouts import LayoutChannelColumnComposer, LayoutZStackColumnComposer, LayoutCompositeComposer

sys.path.append(Path(os.path.realpath(__file__)).parent.parent.parent.as_posix())

from fileops.export.config import read_config
from fileops.logger import get_logger, silence_loggers

log = get_logger(name='render-movie')


def render_movie(mov: ConfigMovie, overwrite=False, parallel=False):
    if len(mov.image_file.frames) == 1:
        log.warning("only one frame, skipping static image")
        return
    elif len(mov.image_file.frames) > 1:
        mv_kwargs = dict(overwrite=overwrite)
        # what follows is a list of supported layouts
        if mov.layout in [f"z-{n}-col" for n in range(1, 9)]:
            cols = min(int(mov.layout.split("-")[1]), mov.image_file.n_zstacks)
            lytcomposer = LayoutZStackColumnComposer(mov, n_columns=cols, **mv_kwargs)
        elif mov.layout in ["twoch", "two-ch", "two-col"]:
            lytcomposer = LayoutChannelColumnComposer(mov, n_columns=2, **mv_kwargs)
        elif mov.layout == "twoch-comp":
            lytcomposer = LayoutCompositeComposer(mov, **mv_kwargs)
        else:
            raise ValueError(f"No supported layout in the rendering of {mov.movie_filename}.")

        lytcomposer.render(parallel=parallel | True)  # set temporarily for debug purposes


def render_movie_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        show_file_info: Annotated[
            bool, typer.Argument(help="To show file metadata information before rendering the movie")] = True,
        overwrite_movie_file: Annotated[
            bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
):
    if cfg_path.parent.name[0:3] == "bad":
        return
    log.info(f"Reading configuration file {cfg_path}")
    cfg = read_config(cfg_path)

    # make movies specified in configuration file
    for mov in cfg.movies:
        silence_loggers(loggers=[mov.image_file.__class__.__name__], output_log_file="silenced.log")
        if show_file_info:
            try:
                log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
            except Exception as e:
                log.error(e)
        render_movie(mov, overwrite=overwrite_movie_file)
