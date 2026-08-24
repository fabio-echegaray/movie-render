from pathlib import Path

import traceback
import typer
from typing_extensions import Annotated

from movierender.layouts import render_static_montage

from fileops.export.config import read_config
from fileops.logger import get_logger

log = get_logger(name='render-panel')


def render_panel_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        with_root_path: Annotated[
            Path, typer.Option(
                help="Path where the image file should be looked in if the path in the configuration file is relative. "
                     "If no path is given, the current folder will be used.")] = None,
        show_file_info: Annotated[
            bool, typer.Option(help="To show file metadata information before rendering the movie")] = True,
        # overwrite_file: Annotated[
        #     bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
        defaults_file: Annotated[
            Path, typer.Option(help="Path to a project-level defaults file whose [DEFAULT] section "
                                    "applies to all sections of the configuration file. If not given, "
                                    "a file named 'defaults.cfg' in the current folder is used if it exists.")] = None,
):
    if cfg_path.parent.name[0:3] == "bad":
        return

    if defaults_file is None:
        log.debug(f"Found file with default information.")
        auto = Path('.') / "defaults.cfg"
        if auto.exists():
            defaults_file = auto.absolute()

    log.info(f"Reading configuration file {cfg_path}")
    cfg = read_config(cfg_path, with_root_path=with_root_path, defaults_file=defaults_file)

    if not hasattr(cfg, "panels") or len(cfg.panels) == 0:
        log.warning(f"No panels found in configuration file.")
        exit(65)  # return code for data format error

    # render panels specified in configuration file
    for pan in cfg.panels:
        if show_file_info:
            try:
                log.info(f"file {cfg_path}\r\n{pan.image_file.info.squeeze(axis=0)}")
            except Exception as e:
                log.error(e)
                log.error(traceback.format_exc())

        render_static_montage(pan, copyright_info=cfg.copyright)
