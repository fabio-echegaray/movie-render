from pathlib import Path
from typing import List, Dict, Union, Iterable, TYPE_CHECKING
from typing import NamedTuple

from fileops.image import ImageFile
from roifile import ImagejRoi

if TYPE_CHECKING:
    from movierender.overlays import Overlay


class ConfigMovie(NamedTuple):
    header: str
    configfile: Path
    series: int
    frames: Iterable[int]
    channels: List[int]
    channel_render_parameters: Dict
    zstack_fn: str
    scalebar: float
    override_dt: Union[float, None]
    image_file: Union[ImageFile, None]
    roi: ImagejRoi
    um_per_z: float
    title: str
    fps: int
    bitrate: str  # bitrate in a format that ffmpeg understands
    movie_filename: str
    layout: str
    include_tracks: Union[str, bool]
    overlays: List['Overlay'] | None
