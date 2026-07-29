import signal
from pathlib import Path

import typer
import fileops
from fileops.export.config import search_config_files
from fileops.logger import get_logger
from typing_extensions import Annotated

from movierender.scripts.render import render_configuration_file_cmd

log = get_logger(name='render-folder')


def _handle_first_sigint(signum, frame):
    fileops.__STOP_REQUESTED.set()
    log.warning("Interrupted — finishing current render and stopping.")
    signal.signal(signal.SIGINT, _handle_second_sigint)


def _handle_second_sigint(signum, frame):
    fileops.__THREAD_STOP_REQUESTED.set()
    signal.signal(signal.SIGINT, signal.default_int_handler)
    raise KeyboardInterrupt()


def render_folder_cmd(
        path: Annotated[
            Path, typer.Argument(help="Path where configuration files are located. "
                                      "If no path is given, the current folder will be used.")] = None,
        with_root_path: Annotated[
            Path, typer.Option(
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

    if len(cfg_path_list)==0:
        log.warning("No configuration files were found.")
    total_rendered = 0
    fileops.__STOP_REQUESTED.clear()
    signal.signal(signal.SIGINT, _handle_first_sigint)

    for cfg_path in cfg_path_list:
        if cfg_path.parent.name[0:3] == "bad":
            continue

        log.info(f"Reading configuration file {cfg_path}")
        try:
            render_configuration_file_cmd(cfg_path,
                                          overwrite_file=overwrite_files,
                                          with_root_path=with_root_path,
                                          run_test=run_test)
            total_rendered += 1
        except KeyboardInterrupt:
            break
        except FileNotFoundError as e:
            log.error(e)
        except Exception as e:
            if fileops.__STOP_REQUESTED.is_set():
                log.warning(f"Render interrupted: {e}")
                break
            raise

        if fileops.__STOP_REQUESTED.is_set():
            break

    signal.signal(signal.SIGINT, signal.default_int_handler)
    return total_rendered
