import logging
from typing import TYPE_CHECKING, Union, List, Set, Iterable

import numpy as np
from fileops.image.ops import ZProjection

from movierender.colorize import DEFAULT_DEPTH_CMAP
from movierender.render.pipelines import PipelineException

if TYPE_CHECKING:
    from movierender.render import MovieRenderer


class ImagePipeline:
    """Base class for all image-rendering pipelines.

    A pipeline turns one image into the array that will be displayed on a
    matplotlib :class:`~matplotlib.axes.Axes`.  Concrete subclasses implement
    :meth:`__call__`; examples are :class:`SingleImage` (a single z-plane),
    :class:`ZProjectionImage` (a z-projection of one channel, including
    depth-coding) and :class:`CompositeRGBImage` (merging several channels
    into one RGB image).

    ``zstack`` semantics (regexp to :class:`fileops.image.ops.ZProjection`):
        * a non-negative ``int``  → a single z-plane
        * a ``list``/``set``/iterable → the (sub)set of z-planes to use
        * ``'all'`` or ``'all-<fn>'`` → the whole stack, projected with ``<fn>``
          (``max``, ``min``, ``mean``, ...)

    ``zstack_fn`` selects how the z-planes are combined (``'max'`` by default).
    ``'depth'``/``'code'`` are *not* projection types (reducers over z); they
    are a rendering convention that requests depth-coding, which is handled by
    :class:`ZProjectionImage` alone (see :mod:`movierender.colorize`).
    ``zstack_cmap`` is the colormap used for that depth-coding and is only
    consumed by depth-capable pipelines.
    """

    def __init__(self, *args, ax=None,
                 zstack: Union[int, List, Set, Iterable, str] = "all",
                 zstack_fn: str | None = None,
                 zstack_cmap: str = DEFAULT_DEPTH_CMAP,
                 **kwargs):
        self._kwargs = kwargs
        self.ax = ax
        if isinstance(zstack, np.integer):
            zstack = int(zstack)
        self.zstack = zstack if isinstance(zstack, int) and zstack >= 0 \
            else zstack if isinstance(zstack, (set, list, Iterable)) else "all"
        self.zstack_cmap = zstack_cmap
        self.zstack_fn = zstack_fn if zstack_fn is not None \
            else None if zstack_fn is None and isinstance(zstack, int) \
            else ZProjection(zstack).name if isinstance(zstack, int) and zstack < 0 \
            else "max"
        self.logger = logging.getLogger(__name__)

        from movierender.render import MovieRenderer
        if len(args) > 0 and isinstance(args[0], MovieRenderer):
            self._renderer = args[0]
        else:
            self._renderer = None

        super().__init__()

    def __radd__(self, ovrl):
        from movierender.render import MovieRenderer
        if isinstance(ovrl, MovieRenderer):
            ovrl_pipeline_filled = len(ovrl.image_pipeline) > 0
            ovrl_pipeline_empty = not ovrl_pipeline_filled
            at_least_one_ax_in_pipeline = ovrl_pipeline_filled and all([ip.ax is None for ip in ovrl.image_pipeline])
            if (ovrl_pipeline_empty and at_least_one_ax_in_pipeline) \
                    or (ovrl_pipeline_filled and self.ax is None):
                raise PipelineException(
                    f"More than one image processing pipeline when adding {ovrl.__class__.__name__}. "
                    "If you need to add more image pipelines, "
                    "consider providing an ax parameter to the class constructor.")
            else:
                if len(ovrl.image.frames) <= 0:
                    raise ValueError("No images to process.")
                ovrl.image_pipeline.append(self)
                self._renderer = ovrl
                return ovrl
        return self

    def __call__(self, *args, **kwargs):
        raise NotImplementedError
