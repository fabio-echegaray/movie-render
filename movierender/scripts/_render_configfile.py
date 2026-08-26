from pathlib import Path

import numpy as np
import traceback
import typer
from typing_extensions import Annotated

import fileops

from movierender.layouts import render_static_montage
from movierender.scripts._render_movie import render_movie
from movierender.scripts._render_projection import render_projection

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
        defaults_file: Annotated[
            Path, typer.Option(help="Path to a project-level defaults file whose [DEFAULT] section "
                                    "applies to all sections of the configuration file. If not given, "
                                    "a file named 'defaults.cfg' in the current folder is used if it exists.")] = None,
):
    if cfg_path.is_dir():
        raise typer.BadParameter(
            "this is a directory; use 'movierender folder' to render configuration files in it",
            param_hint="cfg_path",
        )

    if cfg_path.parent.name[0:3] == "bad":
        return

    if defaults_file is None:
        auto = Path('.') / "defaults.cfg"
        if auto.exists():
            defaults_file = auto.absolute()

    try:
        log.info(f"Reading configuration file {cfg_path}")
        if not overwrite_file:
            chk = check_if_output_files_are_created(cfg_path, with_root_path=with_root_path,
                                                    defaults_file=defaults_file)
            if np.all([created for i, created in chk.items()]):
                log.warning(f"All files are already created from configuration file {cfg_path}")
                return
        cfg = read_config(cfg_path, with_root_path=with_root_path, defaults_file=defaults_file)
    except UnicodeDecodeError as e:
        log.error(f"Invalid file format: {cfg_path} ({e}).")
        return

    # cache the info of each media file so sections sharing the same file
    # (movies, panels, projections) do not re-query it
    _MISSING = object()
    info_cache: dict = {}

    def _log_file_info(image_file):
        if not show_file_info:
            return
        info = info_cache.get(image_file, _MISSING)
        if info is _MISSING:
            info = image_file.info
            info_cache[image_file] = info
        try:
            log.info(f"file {cfg_path}\r\n{info.squeeze(axis=0)}")
        except Exception as e:
            log.error(e)
            log.error(traceback.format_exc())

    # make movies specified in configuration file
    if hasattr(cfg, 'movies'):  # attribute gets added by the plugin system should the file have a valid movie section
        for mov in cfg.movies:
            if fileops.__STOP_REQUESTED.is_set():
                log.info("Stop requested, skipping remaining movies.")
                break
            _log_file_info(mov.image_file)
            try:
                render_movie(mov, overwrite=overwrite_file, test=run_test)
            except FileExistsError:
                if not overwrite_file:
                    log.warning(f"file {mov.movie_filename} already exists in folder.")

    # render panels specified in configuration file
    if hasattr(cfg, 'panels'):  # attribute gets added by the plugin system should the file have a valid movie section
        for pan in cfg.panels:
            _log_file_info(pan.image_file)
            render_static_montage(pan, copyright_info=cfg.copyright)

    # render projections specified in configuration file
    if hasattr(cfg, 'projections'):
        for prj in cfg.projections:
            _log_file_info(prj.image_file)
            render_projection(prj, overwrite=overwrite_file)
