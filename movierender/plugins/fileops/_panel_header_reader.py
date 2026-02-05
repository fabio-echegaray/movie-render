import copy
from typing import List

import fileops
from fileops.export.config_channel_section import update_channel_config_with_section_overrides
from fileops.export.config_sections import process_overrides_of_section
from fileops.logger import get_logger
from fileops.plugins import HeaderReaderPlugin

from movierender.config import ConfigPanel

_rowcol_dict = {
    "channel":  "channel",
    "channels": "channel",
    "frame":    "frame",
    "frames":   "frame",
    "row":      "row",
    "rows":     "row",
    "column":   "column",
    "columns":  "column"
}


class PanelHeaderReaderPlugin(HeaderReaderPlugin):
    log = get_logger(name='PanelHeaderReaderPlugin')

    def has_valid_header(self):
        self._headers = [s for s in self._cfg.sections() if s[:5].upper() == "PANEL"]
        if len(self._headers) > 0:
            return True
        else:
            self.log.debug(f"No headers of type PANEL in file {self._cfg_path}.")
            return False

    def process(self) -> List[ConfigPanel]:
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
                    cinst = clz(self._cfg_path)
                    if cinst.has_valid_header():
                        overlays.extend(cinst.process())

        # process PANEL sections
        panel_def = list()
        for pan in self._headers:
            title = cfg[pan]["title"] if "title" in cfg[pan] else ""
            filename = cfg[pan]["filename"]
            sec_param_override = process_overrides_of_section(cfg[pan], copy.deepcopy(param_override), img_file)
            sec_param_override = update_channel_config_with_section_overrides(sec_param_override, cfg[pan])

            if len(sec_param_override.frames) == 0:
                raise ValueError(f"No frames to render in panel section {pan}.")

            # find overlays
            if "overlays" in cfg[pan]:
                ovr_txt = cfg[pan]["overlays"]
                if ovr_txt[0] == "[" and ovr_txt[-1] == "]":
                    ovr_ids = ovr_txt[1:-1].split(",")

            panel_def.append(ConfigPanel(
                header=pan,
                configfile=self._cfg_path,
                # series=int(cfg["DATA"]["series"]) if "series" in cfg["DATA"] else -1,
                series=img_file.series,
                frames=sec_param_override.frames,
                channels=sec_param_override.channels,
                channel_render_parameters=sec_param_override.channel_info,
                zstacks=sec_param_override.zstacks,
                zstack_fn=cfg[pan]["overlays"] if "overlays" in cfg[pan] else "all-max",
                scalebar=int(cfg[pan]["scalebar"]) if "scalebar" in cfg[pan] else None,
                scalebar_thickness=float(cfg[pan]["scalebar_thickness"]) if "scalebar_thickness" in cfg[pan] else 1,
                draw_scalebar_text=cfg[pan]["draw_scalebar_text"].lower() in ["true", "yes"],
                override_dt=sec_param_override.dt,
                image_file=img_file,
                um_per_z=float(cfg["DATA"]["um_per_z"]) if "um_per_z" in cfg["DATA"] else img_file.um_per_z,
                max_columns=int(cfg[pan]["max_columns"]) if "max_columns" in cfg[pan] else 60,
                max_plots_per_page=int(cfg[pan]["max_plots_per_page"]) if "max_plots_per_page" in cfg[pan] else 40,
                columns=_rowcol_dict[cfg[pan]["columns"]],
                rows=_rowcol_dict[cfg[pan]["rows"]],
                width=float(cfg[pan]["width"]) if "width" in cfg[pan] else 2,
                height=float(cfg[pan]["height"]) if "height" in cfg[pan] else 2,
                roi=roi,
                type=cfg[pan]["layout"] if "layout" in cfg[pan] else "all-frames",
                author=cfg[pan]["author"] if "author" in cfg[pan] else "",
                title=title,
                description=cfg[pan]["description"] if "description" in cfg[pan] else "",
                timestamp_format=cfg[pan]["timestamp_format"] if "timestamp_format" in cfg[pan] else "hh:mm:ss",
                draw_frame_in_timestamp=cfg[pan]["draw_frame_in_timestamp"].lower() in ["true", "yes"]
                if "timestamp_format" in cfg[pan] else False,
                filename=filename,
                layout=cfg[pan]["layout"] if "layout" in cfg[pan] else "all-frames",
                fontsize=cfg[pan]["fontsize"] if "fontsize" in cfg[pan] else 7,
                overlays=[ovr for ovr in overlays if ovr.id in ovr_ids]
            ))
        return panel_def
