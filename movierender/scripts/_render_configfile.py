import os
import sys
from pathlib import Path

import typer
from typing_extensions import Annotated

from movierender.layouts import render_static_montage
from movierender.scripts._render_movie import render_movie

sys.path.append(Path(os.path.realpath(__file__)).parent.parent.parent.as_posix())

from fileops.export.config import read_config
from fileops.logger import get_logger, silence_loggers

log = get_logger(name='render-movie')


def render_configuration_file_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        with_root_path: Annotated[
            Path, typer.Argument(
                help="Path where the image file should be looked in if the path in the configuration file is relative. "
                     "If no path is given, the current folder will be used.")] = None,
        show_file_info: Annotated[
            bool, typer.Argument(help="To show file metadata information before rendering the movie")] = True,
        overwrite_movie_file: Annotated[
            bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
        run_test: Annotated[
            bool, typer.Option(help="Only render first frame when rendering a movie")] = False,
):
    if cfg_path.parent.name[0:3] == "bad":
        return

    log.info(f"Reading configuration file {cfg_path}")
    cfg = read_config(cfg_path, with_root_path=with_root_path)

    # make movies specified in configuration file
    if hasattr(cfg, 'movies'):  # attribute gets added by the plugin system should the file have a valid movie section
        for mov in cfg.movies:
            silence_loggers(loggers=[mov.image_file.__class__.__name__],
                            output_log_file=Path(os.getcwd()) / "silenced.log")
            if show_file_info:
                try:
                    log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
                except Exception as e:
                    log.error(e)
            try:
                render_movie(mov, overwrite=overwrite_movie_file, test=run_test)
            except FileExistsError:
                if not overwrite_movie_file:
                    log.warning(f"file {mov.movie_filename} already exists in folder.")

    # render panels specified in configuration file
    if hasattr(cfg, 'panels'):  # attribute gets added by the plugin system should the file have a valid movie section
        for pan in cfg.panels:
            silence_loggers(loggers=[pan.image_file.__class__.__name__],
                            output_log_file=Path(os.getcwd()) / "silenced.log")
            if show_file_info:
                try:
                    log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
                except Exception as e:
                    log.error(e)
            render_static_montage(pan, copyright_info=cfg.copyright)
