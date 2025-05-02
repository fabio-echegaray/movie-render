from pathlib import Path

import typer
from fileops.export.config import search_config_files
from fileops.logger import get_logger
from typing_extensions import Annotated

from movierender.scripts._render_movie import render_configuration_file

log = get_logger(name='search-folder')


def render(
        path: Annotated[
            Path, typer.Argument(help="Path where configuration files are located. "
                                      "If no path is given, the current folder will be used.")] = None,
):
    if path is None:
        log.info(f"No path provided")
        path = Path('.').absolute()
    cfg_path_list = search_config_files(path)

    for cfg_path in cfg_path_list:
        if cfg_path.parent.name[0:3] == "bad":
            continue

        log.info(f"Reading configuration file {cfg_path}")
        render_configuration_file(cfg_path)
