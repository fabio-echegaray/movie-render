"""Configuration parameters for movie rendering."""

from pathlib import Path
from typing import List, Dict, Union, TYPE_CHECKING, NamedTuple


from fileops.image import ImageFile
from roifile import ImagejRoi

if TYPE_CHECKING:
    from movierender.overlays import Overlay
    from fileops.export.config import ConfigCopyright
    from movierender.config import (
        TextProperties, LineProperties, BackgroundProperties
    )


class ConfigMovie(NamedTuple):
    """Movie config includes graphics as separate parameter for title/font/colors.""" 
    
    header: str
    configfile: Path
    series: int
    frames: List[int]
    channels: List[int]
    channel_render_parameters: Dict
    zstack: List[int]
    zstack_fn: str
    scalebar: float
    override_dt: Union[float, None]
    image_file: Union[ImageFile, None]
    roi: ImagejRoi | List[ImagejRoi] | List[str]
    um_per_z: float
    title: str
    description: str
    fps: int
    bitrate: str  # bitrate in a format that ffmpeg understands
    movie_filename: str
    layout: str
    include_tracks: Union[str, bool]
    # Graphics parameters
    scalebar_text: Union['TextProperties', None] = None
    scalebar_line: Union['LineProperties', None] = None
    timestamp: Union['TextProperties', None] = None
    channel_label: Union['TextProperties', None] = None
    suptitle: Union['TextProperties', None] = None
    background: Union['BackgroundProperties', None] = None
    overlays: List['Overlay'] | None = None
    copyright: Union["ConfigCopyright", None] = None
    max_width: int = 2880
