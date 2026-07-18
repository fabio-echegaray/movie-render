from typing import Iterable

import matplotlib.colors as mcolors
import numpy as np
from fileops.image import ImageFile
from fileops.image.ops import normalize_to_dtype, rescale
from skimage import color

from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class CompositeRGBImage(ImagePipeline):
    def _img(self, channel, image_file=None, frame=None):
        imf = self._renderer.image if image_file is None else image_file
        frame = self._renderer.frame if frame is None else frame

        if type(self.zstack) is int and self.zstack >= 0:
            ix = imf.ix_at(c=channel, z=self.zstack, t=frame)
            self.logger.debug(f"Retrieving frame {frame} of channel {channel} at z-stack={self.zstack} "
                              f"(index={ix})")
            mdi = imf.image(ix)
            return mdi.image if mdi is not None else None
        elif type(self.zstack) is int and self.zstack < 0:
            self.logger.debug(f"Retrieving max z projection of frame {frame} and channel {channel}")
            mdi = imf.z_projection(frame=frame, channel=channel, projection=self.zstack)
            return mdi.image if mdi is not None else None
        elif isinstance(self.zstack, (list, set, Iterable)):
            self.logger.debug(f"Retrieving max z projection of frame {frame} and channel {channel}")
            mdi = imf.z_projection(frame=frame, channel=channel, z_subset=self.zstack, projection=self.zstack_fn)
            return mdi.image if mdi is not None else None
        elif type(self.zstack) is str:
            if self.zstack.split("-")[1] in ["max", "min", "sum", "std", "avg", "mean", "median", ]:  # max projection
                self.logger.debug(f"Retrieving max z projection of frame {frame} and channel {channel}")
                mdi = imf.z_projection(frame=frame, channel=channel, projection=self.zstack)
                return mdi.image if mdi is not None else None
        return None

    def __call__(self, *args, **kwargs):
        if 'channeldict' not in self._kwargs:
            raise Exception("Channel parameters needed to apply this pipeline.")
        channeldict = self._kwargs['channeldict']

        # check if an ImageFile object is provided as an argument. Use that if provided, otherwise use the renderer.
        if len(args) > 0 and isinstance(args[0], ImageFile):
            imf = args[0]
        elif hasattr(self, "_renderer") and self._renderer is not None:
            imf = self._renderer.image
        else:
            raise ValueError("No image source to render from.")
        # check if frame is provided as an argument. Use that if provided, otherwise use the renderer.
        _frame = kwargs.get("frame", self._renderer.frame if self._renderer is not None else 0)

        dtype = None
        background = np.zeros((imf.height, imf.width) + (3,), dtype=np.float64)
        for name, settings in channeldict.items():
            channel = settings['id']
            _img = self._img(channel, image_file=imf if self._renderer is None else None, frame=_frame)
            if _img is None:
                continue
            if dtype is None:
                dtype = _img.dtype

            rgb_vector_color = mcolors.to_rgb(settings['color'])
            if not isinstance(rgb_vector_color, tuple):
                raise TypeError("color must be convertible to RGB tuple.")

            _img = color.gray2rgb(_img)
            background += _img * rgb_vector_color * settings['intensity']

        return normalize_to_dtype(background, dtype) if dtype is not None else background
