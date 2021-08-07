import logging
import numpy as np
from skimage import color, exposure


class ImagePipeline(object):
    def __init__(self, *args, ax=None, **kwargs):
        self._kwargs = kwargs
        self.ax = ax
        self.logger = logging.getLogger(__name__)

        # if len(args) > 0 and isinstance(args[0], MovieRenderer):
        if len(args) > 0 and args[0].__class__.__name__ == 'MovieRenderer':
            self._renderer = args[0]
        else:
            self._renderer = None

    def __radd__(self, ovrl):
        # if isinstance(ovrl, MovieRenderer):
        if ovrl.__class__.__name__ == 'MovieRenderer':
            if ovrl.image_pipeline is not None:
                raise Exception("More than one image processing pipeline.")
            else:
                assert len(ovrl.image.frames) > 0, "No images to process."
                ovrl.image_pipeline = self
                self._renderer = ovrl
                return ovrl
        return self


class SingleImage(ImagePipeline):
    def __call__(self, *args, **kwargs):
        channel = zstack = 0
        r = self._renderer

        ix = r.image.ix_at(c=channel, z=zstack, t=r.frame - 1)
        self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={zstack} "
                          f"(index={ix})")
        mimg = r.image.image(ix)
        return mimg.image if mimg is not None else np.zeros((r.width, r.height))


class CompositeRGBImage(ImagePipeline):
    def __call__(self, *args, **kwargs):
        zstack = 0

        if 'channeldict' not in self._kwargs:
            raise Exception("Channel parameters needed to apply this pipeline.")
        channeldict = self._kwargs['channeldict']

        r = self._renderer

        background = np.zeros((r.width, r.height) + (3,), dtype=np.float64)
        for name, settings in channeldict.items():
            channel = settings['id']
            ix = r.image.ix_at(c=channel, z=zstack, t=r.frame - 1)
            self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={zstack} "
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
