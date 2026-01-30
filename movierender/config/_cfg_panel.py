from pathlib import Path
from typing import List, Dict, Union
from typing import NamedTuple

from fileops.image import ImageFile
from roifile import ImagejRoi


class ConfigPanel(NamedTuple):
    header: str
    configfile: Path
    series: int
    frames: List[int]
    channels: List[int]
    channel_render_parameters: Dict
    zstacks: List[int]
    scalebar: float
    override_dt: Union[float, None]
    image_file: Union[ImageFile, None]
    roi: ImagejRoi
    columns: str
    rows: str
    type: str
    um_per_z: float
    title: str
    filename: str
    layout: str
