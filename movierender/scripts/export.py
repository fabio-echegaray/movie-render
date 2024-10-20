import os
import sys
from pathlib import Path

sys.path.append(Path(os.path.realpath(__file__)).parent.parent.parent.as_posix())

from fileops.export.config import read_config, search_config_files
from fileops.logger import get_logger, silence_loggers
from movierender.layouts.two_channels import make_movie as make_movie_2ch
from movierender.layouts.two_ch_composite import make_movie as make_movie_2ch_comp

log = get_logger(name='export')
silence_loggers(loggers=["tifffile"])

if __name__ == "__main__":
    cfg_path_list = search_config_files(Path("/media/lab/cache/export/Nikon/"))

    silence_loggers(loggers=["tifffile", "movierender", "PIL"], output_log_file="silenced.log")

    for cfg_path in cfg_path_list:
        if cfg_path.parent.name[0:3] == "bad":
            continue
        try:
            log.info(f"Reading configuration file {cfg_path}")
            cfg = read_config(cfg_path)
            silence_loggers(loggers=[cfg.image_file.__class__.__name__], output_log_file="silenced.log")

            channels = dict()

            # make movie
            if len(cfg.image_file.frames) > 1:
                mv_kwargs = dict(zstack="all-max",
                                 fig_title=cfg.title,
                                 fps=cfg.fps,
                                 prefix=cfg.path.name + "-",
                                 name=cfg.movie_filename,
                                 folder=cfg_path.parent.parent)
                if cfg.layout in ["twoch", "two-ch"]:
                    make_movie_2ch(cfg.image_file, **mv_kwargs)
                elif cfg.layout == "twoch-comp":
                    make_movie_2ch_comp(cfg.image_file, **mv_kwargs)
            elif len(cfg.image_file.frames) == 1:
                log.warning("only one frame, skipping static image")

        except Exception as e:
            import traceback

            print(traceback.format_exc())
