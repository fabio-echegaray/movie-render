import matplotlib

matplotlib.use("Agg")

from .render import MovieRenderer, ImagePipeline, SingleImage, CompositeRGBImage, NullImage  # noqa

import matplotlib.pyplot as plt  # noqa
from matplotlib import gridspec  # noqa
