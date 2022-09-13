import logging
from uuid import uuid4

import numpy as np
from skimage import color, exposure

from fileops.image.imagemeta import MetadataImage


class PipelineException(Exception):
    pass


class ImagePipeline:
    def __init__(self, *args, ax=None, zstack=0, **kwargs):
        self.uuid = uuid4()
        self._kwargs = kwargs
        self.ax = ax
        self.zstack = zstack
        self.logger = logging.getLogger(__name__)

        # if len(args) > 0 and isinstance(args[0], MovieRenderer):
        if len(args) > 0 and args[0].__class__.__name__ == 'MovieRenderer':
            self._renderer = args[0]
        else:
            self._renderer = None

    def __radd__(self, ovrl):
        # if isinstance(ovrl, MovieRenderer):
        if ovrl.__class__.__name__ == 'MovieRenderer':
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
                assert len(ovrl.image.frames) > 0, "No images to process."
                ovrl.image_pipeline.append(self)
                self._renderer = ovrl
                return ovrl
        return self

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class SingleImage(ImagePipeline):
    def __call__(self, *args, channel=0, adjust_exposure=True, **kwargs):
        r = self._renderer

        ix = r.image.ix_at(c=channel, z=self.zstack, t=r.frame)
        self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={self.zstack} "
                          f"(index={ix})")
        mimg = r.image.image(ix)
        img = mimg.image if (type(mimg) == MetadataImage and mimg.image is not None) else np.zeros((r.width, r.height))
        if adjust_exposure:
            p2, p98 = np.percentile(img, (2, 98))
            img = exposure.rescale_intensity(img, in_range=(p2, p98))
        return img


class CompositeRGBImage(ImagePipeline):
    def __call__(self, *args, **kwargs):
        if 'channeldict' not in self._kwargs:
            raise Exception("Channel parameters needed to apply this pipeline.")
        channeldict = self._kwargs['channeldict']

        r = self._renderer

        background = np.zeros(r.image.image(0).image.shape + (3,), dtype=np.float64)
        for name, settings in channeldict.items():
            channel = settings['id']
            ix = r.image.ix_at(c=channel, z=self.zstack, t=r.frame)
            self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={self.zstack} "
                              f"(index={ix})")

            _img = r.image.image(ix).image

            # Contrast enhancing by stretching the histogram
            if 'rescale' in settings:
                if hasattr(r, 'ranges'):
                    mini, maxi = r.ranges[channel * 2], r.ranges[channel * 2 + 1]
                    _img = exposure.rescale_intensity(_img, in_range=(mini, maxi))
                else:
                    _img = exposure.rescale_intensity(_img, in_range=tuple(np.percentile(_img, (2, 99))))

            _img = color.gray2rgb(_img)
            background += _img * settings['color'] * settings['intensity']

        return exposure.rescale_intensity(background)
