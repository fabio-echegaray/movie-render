from pathlib import Path
from typing import List, Dict, Union, TYPE_CHECKING
from typing import NamedTuple

from fileops.image import ImageFile
from roifile import ImagejRoi

if TYPE_CHECKING:
    from movierender.overlays import OverlayPlugin


class ConfigPanel(NamedTuple):
    header: str
    configfile: Path
    series: int
    frames: List[int]
    channels: List[int]
    channel_render_parameters: Dict
    zstacks: List[int]
    zstack_fn: str
    scalebar: float
    scalebar_thickness: float
    draw_scalebar_text: bool
    override_dt: Union[float, None]
    image_file: Union[ImageFile, None]
    roi: ImagejRoi
    columns: str
    max_columns: int
    max_plots_per_page: int
    width: float
    height: float
    rows: str
    type: str
    multipage: bool
    um_per_z: float
    author: str
    title: str
    description: str
    timestamp_format: str
    draw_frame_in_timestamp: bool
    filename: str
    layout: str
    fontsize: int
    overlays: List['OverlayPlugin'] | None
