import os
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

from layouts import render_static_montage

sys.path.append(Path(os.path.realpath(__file__)).parent.parent.parent.as_posix())

from fileops.export.config import read_config
from fileops.logger import get_logger, silence_loggers

log = get_logger(name='render-panel')


def render_panel_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        show_file_info: Annotated[
            bool, typer.Argument(help="To show file metadata information before rendering the movie")] = True,
        # overwrite_movie_file: Annotated[
        #     bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
):
    if cfg_path.parent.name[0:3] == "bad":
        return

    log.info(f"Reading configuration file {cfg_path}")
    cfg = read_config(cfg_path)

    # render panels specified in configuration file
    for pan in cfg.panels:
        silence_loggers(loggers=[pan.image_file.__class__.__name__], output_log_file="silenced.log")
        if show_file_info:
            log.info(f"file {cfg_path}\r\n{pan.image_file.info.squeeze(axis=0)}")
        render_static_montage(pan, row=pan.rows, col=pan.columns)
