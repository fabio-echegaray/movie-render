from pathlib import Path

import typer
from fileops.export.config import search_config_files
from fileops.logger import get_logger
from typing_extensions import Annotated

from movierender.scripts.render import render_configuration_file_cmd

log = get_logger(name='render-folder')


def render_folder_cmd(
        path: Annotated[
            Path, typer.Argument(help="Path where configuration files are located. "
                                      "If no path is given, the current folder will be used.")] = None,
        with_root_path: Annotated[
            Path, typer.Argument(
                help="Path where image files should be looked in if the path in the configuration file is relative. "
                     "If no path is given, the current folder will be used.")] = None,
        overwrite_files: Annotated[
            bool, typer.Option(help="Set true if you want to overwrite the files")] = False,
        run_test: Annotated[
            bool, typer.Option(help="Only render first frame when rendering a movie")] = False,
):
    if path is None:
        log.info(f"No path provided")
        path = Path('.').absolute()
    cfg_path_list = search_config_files(path)

    total_rendered = 0
    for cfg_path in cfg_path_list:
        if cfg_path.parent.name[0:3] == "bad":
            continue

        log.info(f"Reading configuration file {cfg_path}")
        try:
            render_configuration_file_cmd(cfg_path,
                                          overwrite_movie_file=overwrite_files,
                                          with_root_path=with_root_path,
                                          run_test=run_test)
            total_rendered += 1
        except FileNotFoundError as e:
            log.error(e)

    return total_rendered
