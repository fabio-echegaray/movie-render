import os
import sys
from pathlib import Path

import numpy as np
import typer
from typing_extensions import Annotated

from movierender.layouts import render_static_montage
from movierender.scripts._render_movie import render_movie
from movierender.scripts._render_projection import render_projection

sys.path.append(Path(os.path.realpath(__file__)).parent.parent.parent.as_posix())

from fileops.export.config import read_config, check_if_output_files_are_created
from fileops.logger import get_logger

log = get_logger(name='render-movie')


def render_configuration_file_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        with_root_path: Annotated[
            Path, typer.Option(
                help="Path where the image file should be looked in if the path in the configuration file is relative. "
                     "If no path is given, the current folder will be used.")] = None,
        show_file_info: Annotated[
            bool, typer.Option(help="To show file metadata information before rendering the movie")] = True,
        overwrite_file: Annotated[
            bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
        run_test: Annotated[
            bool, typer.Option(help="Only render first frame when rendering a movie")] = False,
):
    if cfg_path.parent.name[0:3] == "bad":
        return

    log.info(f"Reading configuration file {cfg_path}")
    if not overwrite_file:
        chk = check_if_output_files_are_created(cfg_path, with_root_path=with_root_path)
        if np.all([created for i, created in chk.items()]):
            log.warning(f"All files are already created from configuration file {cfg_path}")
            return
    cfg = read_config(cfg_path, with_root_path=with_root_path)

    # make movies specified in configuration file
    if hasattr(cfg, 'movies'):  # attribute gets added by the plugin system should the file have a valid movie section
        for mov in cfg.movies:
            if show_file_info:
                try:
                    log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
                except Exception as e:
                    log.error(e)
            try:
                render_movie(mov, overwrite=overwrite_file, test=run_test)
            except FileExistsError:
                if not overwrite_file:
                    log.warning(f"file {mov.movie_filename} already exists in folder.")

    # render panels specified in configuration file
    if hasattr(cfg, 'panels'):  # attribute gets added by the plugin system should the file have a valid movie section
        for pan in cfg.panels:
            if show_file_info:
                try:
                    log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
                except Exception as e:
                    log.error(e)
            render_static_montage(pan, copyright_info=cfg.copyright)

    # render projections specified in configuration file
    if hasattr(cfg, 'projections'):
        for prj in cfg.projections:
            if show_file_info:
                try:
                    log.info(f"file {cfg_path}\r\n{mov.image_file.info.squeeze(axis=0)}")
                except Exception as e:
                    log.error(e)
            render_projection(prj, overwrite=overwrite_file)
