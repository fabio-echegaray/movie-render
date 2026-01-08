import copy
from typing import List

from fileops.export.config_channel_section import update_channel_config_with_section_overrides
from fileops.export.config_sections import process_overrides_of_section
from fileops.logger import get_logger
from fileops.plugins import HeaderReaderPlugin
from movierender.config._cfg_panel import ConfigPanel

log = get_logger(name='export')

_rowcol_dict = {
    "channel":  "channel",
    "channels": "channel",
    "frame":    "frame",
    "frames":   "frame"
}


class PanelHeaderReaderPlugin(HeaderReaderPlugin):

    def has_valid_header(self):
        self._headers = [s for s in self._cfg.sections() if s[:5].upper() == "PANEL"]
        if len(self._headers) > 0:
            return True
        else:
            log.debug(f"No headers of type PANEL in file {self._cfg_path}.")
            return False

    def process(self) -> List[ConfigPanel]:
        if self._headers is None:
            return []

        cfg, param_override, img_file, roi = self._cfg, self._param_override, self._img_file, self._roi

        # process PANEL sections
        panel_def = list()
        for pan in self._headers:
            title = cfg[pan]["title"]
            filename = cfg[pan]["filename"]
            sec_param_override = process_overrides_of_section(cfg[pan], copy.deepcopy(param_override), img_file)
            sec_param_override = update_channel_config_with_section_overrides(sec_param_override, cfg[pan])

            if len(sec_param_override.frames) == 0:
                raise ValueError(f"No frames to render in panel section {pan}.")

            panel_def.append(ConfigPanel(
                header=pan,
                configfile=self._cfg_path,
                # series=int(cfg["DATA"]["series"]) if "series" in cfg["DATA"] else -1,
                series=img_file.series,
                frames=sec_param_override.frames,
                channels=sec_param_override.channels,
                channel_render_parameters=sec_param_override.channel_info,
                zstacks=sec_param_override.zstacks,
                scalebar=float(cfg[pan]["scalebar"]) if "scalebar" in cfg[pan] else 10,
                override_dt=sec_param_override.dt,
                image_file=img_file,
                um_per_z=float(cfg["DATA"]["um_per_z"]) if "um_per_z" in cfg["DATA"] else img_file.um_per_z,
                columns=_rowcol_dict[cfg[pan]["columns"]],
                rows=_rowcol_dict[cfg[pan]["rows"]],
                roi=roi,
                type=cfg[pan]["layout"] if "layout" in cfg[pan] else "all-frames",
                title=title,
                filename=filename,
                layout=cfg[pan]["layout"] if "layout" in cfg[pan] else "all-frames"
            ))
        return panel_def
