import os
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

sys.path.append(Path(os.path.realpath(__file__)).parent.parent.parent.as_posix())

from fileops.export.config import read_config
from fileops.logger import get_logger, silence_loggers
from movierender.layouts.two_channels import make_movie as make_movie_2ch
from movierender.layouts.two_ch_composite import make_movie as make_movie_2ch_comp

log = get_logger(name='render-movie')


def render_configuration_file(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        show_file_info: Annotated[
            bool, typer.Argument(help="To show file metadata information before rendering the movie")] = True,
        overwrite_movie_file: Annotated[
            bool, typer.Argument(help="Set true if you want to overwrite the file")] = False,
):
    if cfg_path.parent.name[0:3] == "bad":
        return
    try:
        log.info(f"Reading configuration file {cfg_path}")
        cfg = read_config(cfg_path)

        # make movies specified in configuration file
        for mov in cfg.movies:
            silence_loggers(loggers=[mov.image_file.__class__.__name__], output_log_file="silenced.log")
            if show_file_info:
                log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
            if len(mov.image_file.frames) > 1:
                mv_kwargs = dict(zstack="all-max",
                                 fig_title=mov.title,
                                 fps=mov.fps,
                                 prefix=cfg.path.name + "-",
                                 name=mov.movie_filename,
                                 folder=cfg_path.parent.parent,
                                 overwrite=overwrite_movie_file)
                # what follows is a list of supported layouts
                if mov.layout in ["twoch", "two-ch"]:
                    make_movie_2ch(mov.image_file, **mv_kwargs)
                elif mov.layout == "twoch-comp":
                    make_movie_2ch_comp(mov.image_file, **mv_kwargs)
            elif len(mov.image_file.frames) == 1:
                log.warning("only one frame, skipping static image")

    except Exception as e:
        import traceback

        log.error(traceback.format_exc())
        raise e
