import copy
from pathlib import Path
from typing import List, Dict

import fileops
from fileops.export.config_channel_section import update_channel_config_with_section_overrides
from fileops.export.config_sections import process_overrides_of_section
from fileops.logger import get_logger
from fileops.plugins import HeaderReaderPlugin

from movierender.config import ConfigMovie
from movierender.overlays import ImagejROI


def load_overlay_plugins(cfg_path, root_path=None, **shared):
    overlays = list()
    for h in fileops.header_reader_plugins:
        if "overlay" not in h.name:
            continue
        clz = h.load()
        if not issubclass(clz, HeaderReaderPlugin):
            continue
        cinst = clz(cfg_path, root_path=root_path, **shared)
        if cinst.has_valid_header():
            overlays.extend(cinst.process())
    return overlays


class MovieHeaderReaderPlugin(HeaderReaderPlugin):
    log = get_logger(name='MovieHeaderReaderPlugin')

    def has_valid_header(self):
        self._headers = [s for s in self._cfg.sections() if s[:5].upper() == "MOVIE"]
        if len(self._headers) > 0:
            return True
        else:
            self.log.debug(f"No headers of type MOVIE in file {self._cfg_path}.")
            return False

    def header_output_file_exist(self) -> Dict[str, bool]:
        """ check if output file paths exists without loading the whole structure """
        headers = [s for s in self._cfg.sections() if s.upper().startswith("MOVIE")]
        if len(headers) == 0:
            self.log.debug(f"No headers with name MOVIE to check in file {self._cfg_path}.")
            return {"none": False}

        # process sections
        out = {mvh: False for mvh in headers}
        for mov in headers:
            if "filename" in self._cfg[mov]:
                out_name = Path(self._cfg[mov]["filename"] + ".mp4")
                base_path = self._root_path if self._root_path is not None else out_name.parent if out_name.is_absolute() else self._cfg_path.parent
                out_path = base_path / out_name.name
                if out_path.exists():
                    out[mov] = True

        return out

    def process(self) -> List[ConfigMovie]:
        if self._headers is None:
            return []

        cfg, param_override, img_file, roi = self._cfg, self._param_override, self._img_file, self._roi

        # process ROI sections in configuration file
        roi_lst = list()
        for p in fileops.config_type_plugins:
            if "roi" not in p.name:
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
                    # propagate the shared data-section objects to nested plugins
                    cinst = clz(self._cfg_path, root_path=self._root_path,
                                cfg=cfg, img_file=img_file, param_override=param_override, roi=roi)
                    if cinst.has_valid_header():
                        roi_lst.extend(cinst.process())

        # find OVERLAY parsers from plugins
        overlays = load_overlay_plugins(self._cfg_path, root_path=self._root_path,
                                        cfg=cfg, img_file=img_file, param_override=param_override, roi=roi)

        # process MOVIE sections
        movie_def = list()
        for mov in self._headers:
            title = cfg[mov]["title"]
            description = cfg[mov]["description"] if "description" in cfg[mov] else ""
            fps = cfg[mov]["fps"]
            movie_filename = cfg[mov]["filename"] if "filename" in cfg[mov] else "no_filename_given"
            sec_param_override = process_overrides_of_section(cfg[mov], copy.deepcopy(param_override), img_file)
            sec_param_override = update_channel_config_with_section_overrides(sec_param_override, cfg[mov])
            include_tracks = cfg[mov]["include_tracks"] if "include_tracks" in cfg[mov] else None

            # process OVERLAY sections in configuration file
            overlays_to_add = list()
            if "overlays" in cfg[mov]:
                ovr_txt = cfg[mov]["overlays"]
                if ovr_txt[0] == "[" and ovr_txt[-1] == "]":
                    ovr_ids = [s.strip() for s in ovr_txt[1:-1].split(",")]
                    overlays_to_add.extend([ovr for ovr in overlays if ovr.overlay_id in ovr_ids])

            # find ROI IDs and append them to list of ROIs
            if "roi" in cfg[mov]:
                roi_txt = cfg[mov]["roi"]
                if roi_txt[0] == "[" and roi_txt[-1] == "]":
                    roi_ids = [s.strip() for s in roi_txt[1:-1].split(",") if len(s) > 0]
                    if len(roi_ids) > 0:
                        overlays_to_add.extend(ImagejROI(r.geometry) for r in roi_lst if r.header in roi_ids and r.plot)

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
                zstack=sec_param_override.zstacks,
                zstack_fn=cfg[mov]["zstack_fn"] if "zstack_fn" in cfg[mov] else "all-max",
                um_per_z=float(cfg["DATA"]["um_per_z"]) if "um_per_z" in cfg["DATA"] else img_file.um_per_z,
                roi=roi,
                title=title,
                description=description,
                fps=int(fps) if fps else 1,
                bitrate=cfg[mov]["bitrate"] if "bitrate" in cfg[mov] else "500k",
                movie_filename=movie_filename,
                layout=cfg[mov]["layout"] if "layout" in cfg[mov] else "twoch-comp",
                include_tracks=(
                    include_tracks if isinstance(include_tracks, bool)
                    else include_tracks == "yes" if isinstance(include_tracks, str)
                    else False
                ),
                overlays=overlays_to_add
            ))
        return movie_def
