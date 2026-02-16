import copy
from typing import List

import fileops
from fileops.export.config_channel_section import update_channel_config_with_section_overrides
from fileops.export.config_sections import process_overrides_of_section
from fileops.logger import get_logger
from fileops.plugins import HeaderReaderPlugin

from movierender.config import ConfigMovie


class MovieHeaderReaderPlugin(HeaderReaderPlugin):
    log = get_logger(name='MovieHeaderReaderPlugin')

    def has_valid_header(self):
        self._headers = [s for s in self._cfg.sections() if s[:5].upper() == "MOVIE"]
        if len(self._headers) > 0:
            return True
        else:
            self.log.debug(f"No headers of type MOVIE in file {self._cfg_path}.")
            return False

    def process(self) -> List[ConfigMovie]:
        if self._headers is None:
            return []

        cfg, param_override, img_file, roi = self._cfg, self._param_override, self._img_file, self._roi

        # process OVERLAY sections in configuration file
        overlays = list()
        for p in fileops.config_type_plugins:
            if "overlay" not in p.name:
                continue
            self.log.debug(f"Checking {p.name}")
            t_name = p.name
            header_reader_name = f"{t_name}_header_reader"
            for h in fileops.header_reader_plugins:
                if h.name == header_reader_name:
                    self.log.debug(f"Loading {header_reader_name}")
                    clz = h.load()
                    if not issubclass(clz, HeaderReaderPlugin):
                        continue
                    cinst = clz(self._cfg_path, root_path=self._root_path)
                    if cinst.has_valid_header():
                        overlays.extend(cinst.process())

        # process MOVIE sections
        movie_def = list()
        for mov in self._headers:
            title = cfg[mov]["title"]
            fps = cfg[mov]["fps"]
            movie_filename = cfg[mov]["filename"]
            sec_param_override = process_overrides_of_section(cfg[mov], copy.deepcopy(param_override), img_file)
            sec_param_override = update_channel_config_with_section_overrides(sec_param_override, cfg[mov])
            include_tracks = cfg[mov]["include_tracks"] if "include_tracks" in cfg[mov] else None
            # find overlays
            if "overlays" in cfg[mov]:
                ovr_txt = cfg[mov]["overlays"]
                if ovr_txt[0] == "[" and ovr_txt[-1] == "]":
                    ovr_ids = ovr_txt[1:-1].split(",")

            movie_def.append(ConfigMovie(
                header=mov,
                configfile=self._cfg_path,
                series=img_file.series,
                frames=sec_param_override.frames,
                channels=sec_param_override.channels,
                channel_render_parameters=sec_param_override.channel_info,
                scalebar=float(cfg[mov]["scalebar"]) if "scalebar" in cfg[mov] else None,
                override_dt=sec_param_override.dt,
                image_file=img_file,
                zstack_fn=cfg[mov]["zstack_fn"] if "zstack_fn" in cfg[mov] else "all-max",
                um_per_z=float(cfg["DATA"]["um_per_z"]) if "um_per_z" in cfg["DATA"] else img_file.um_per_z,
                roi=roi,
                title=title,
                fps=int(fps) if fps else 1,
                bitrate=cfg[mov]["bitrate"] if "bitrate" in cfg[mov] else "500k",
                movie_filename=movie_filename,
                layout=cfg[mov]["layout"] if "layout" in cfg[mov] else "twoch-comp",
                include_tracks=(
                    include_tracks if type(include_tracks) is bool
                    else include_tracks == "yes" if type(include_tracks) is str
                    else False
                ),
                overlays=[ovr for ovr in overlays if ovr.id in ovr_ids]
            ))
        return movie_def
