from pathlib import Path

import pandas as pd
import traceback
import typer
from typing_extensions import Annotated

from movierender.config import ConfigMovie
from movierender.layouts import LayoutChannelColumnComposer, LayoutZStackColumnComposer, LayoutCompositeComposer

import fileops
from fileops.export.config import read_config
from fileops.logger import get_logger

log = get_logger(name='render-movie')


def render_movie(mov: ConfigMovie, overwrite=False, parallel=False, test=False):
    fileops.reset_shared_state()
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

        lytcomposer.render(parallel=parallel | True, test=test)  # TODO: remove True value set for debugging purposes


def render_movie_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        with_root_path: Annotated[
            Path, typer.Option(
                help="Path where image files should be looked in if the path in the configuration file is relative. "
                     "If no path is given, the current folder will be used.")] = None,
        show_file_info: Annotated[
            bool, typer.Option(help="To show file metadata information before rendering the movie")] = True,
        overwrite_movie_file: Annotated[
            bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
        run_test: Annotated[
            bool, typer.Option(help="Renders first frame only when true")] = False,
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

    # cache the info of each media file so movies sharing the same file are not re-queried
    _MISSING = object()
    info_cache: dict = {}

    # make movies specified in configuration file
    for mov in cfg.movies:
        if show_file_info:
            info = info_cache.get(mov.image_file, _MISSING)
            if info is _MISSING:
                info = mov.image_file.info
                info_cache[mov.image_file] = info
            try:
                with pd.option_context("display.max_columns", None, "display.max_colwidth", None,
                                       "display.width", 1000):
                    log.info(f"file {cfg_path}\r\n{info.squeeze(axis=0)}")
            except Exception as e:
                log.error(e)
                log.error(traceback.format_exc())
        render_movie(mov, overwrite=overwrite_movie_file, test=run_test)
