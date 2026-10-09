import sys

from fileops.logger import get_logger, silence_loggers

# silence third-party loggers before importing them so their DEBUG output is
# not emitted even during module import
silence_loggers(loggers=["tifffile", "matplotlib", "PIL"])

import matplotlib

matplotlib.use("Agg")

from .render import MovieRenderer, ImagePipeline, SingleImage, CompositeRGBImage, NullImage  # noqa

import matplotlib.pyplot as plt  # noqa
from matplotlib import gridspec  # noqa

# check for plugins
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

log = get_logger(name='movierender-plugin-engine')

# load all types
log.info(f"Loading Movie-Render plugins.")
overlay_type_plugins = entry_points(group='movierender.plugins.overlays')
for dp in overlay_type_plugins:
    log.info(f"found plugin of overlay {dp.name} ({dp.value})")
