import ast
from typing import List, Dict

from fileops.logger import get_logger
from fileops.plugins import HeaderReaderPlugin

from movierender.overlays import Overlay
from movierender.overlays._arrow import ArrowOverlayPlugin


class ArrowOverlayHeaderReaderPlugin(HeaderReaderPlugin):
    log = get_logger(name='ArrowOverlayHeaderReaderPlugin')

    def has_valid_header(self):
        self._headers = [s for s in self._cfg.sections() if
                         s.upper().startswith("OVERLAY") and self._cfg[s]["type"] == "arrow"]
        if len(self._headers) > 0:
            return True
        else:
            self.log.debug(f"No OVERLAY headers of type ARROW in file {self._cfg_path}.")
            return False

    def header_output_file_exist(self) -> Dict[str, bool]:
        # return False for all sections
        headers = [s for s in self._cfg.sections() if
                   s.upper().startswith("OVERLAY") and self._cfg[s]["type"] == "arrow"]
        out = {mvh: False for mvh in headers}
        return out

    def process(self) -> List[Overlay]:
        if self._headers is None:
            return []

        cfg, param_override, img_file, roi = self._cfg, self._param_override, self._img_file, self._roi

        # process ARROW overlay sections
        arrow_def = list()
        for arrow in self._headers:
            xy = ast.literal_eval(cfg[arrow]["xy"])
            frame = int(cfg[arrow]["frame"]) if "frame" in cfg[arrow] else None
            z = int(cfg[arrow]["z"]) if "z" in cfg[arrow] else None
            length = float(cfg[arrow]["length"])
            angle = int(cfg[arrow]["angle"])
            color = cfg[arrow]["color"]

            length = length * img_file.pix_per_um

            arrow_def.append(
                ArrowOverlayPlugin(*xy, overlay_id=cfg[arrow]["id"], length=length, angle=angle, frame=frame, z=z, c=color)
            )
        return arrow_def
