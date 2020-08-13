import logging
# from .movie import MovieRenderer
import numpy as np
from skimage import color, exposure


class ImagePipeline(object):
    def __init__(self, *args, **kwargs):
        self._kwargs = kwargs
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
                assert ovrl.images is not None, "No images to process."
                ovrl.image_pipeline = self
                self._renderer = ovrl
                return ovrl
        return self


class SingleImage(ImagePipeline):
    def __call__(self, *args, **kwargs):
        channel = zstack = 1
        r = self._renderer

        ix = r.frame * (r.n_channels * r.n_zstacks) + zstack * r.n_channels + channel
        self.logger.debug(f"Retrieving frame {r.frame} of {channel} at z-stack={zstack} "
                          f"(index={ix} = {r.frame} * ({r.n_channels} * {r.n_zstacks})"
                          f" + {zstack} * {r.n_channels} + {channel})")

        return r.images[ix if ix <= len(r.images) - 1 else len(r.images) - 1]


class CompositeRGBImage(ImagePipeline):
    def __call__(self, *args, **kwargs):
        zstack = 1

        if not 'channeldict' in self._kwargs:
            raise Exception("Channel parameters needed to apply this pipeline.")
        channeldict = self._kwargs['channeldict']

        r = self._renderer

        background = np.zeros((r.width, r.height) + (3,), dtype=np.float64)
        for name, settings in channeldict.items():
            channel = settings['id']
            ix = r.frame * (r.n_channels * r.n_zstacks) + zstack * r.n_channels + channel
            self.logger.debug(f"Retrieving frame {r.frame} of {channel} at z-stack={zstack} "
                              f"(index={ix} = {r.frame} * ({r.n_channels} * {r.n_zstacks})"
                              f" + {zstack} * {r.n_channels} + {channel})")

            _img = r.images[ix if ix <= len(r.images) - 1 else len(r.images) - 1]

            # Contrast enhancing by stretching the histogram
            # _img = exposure.equalize_hist(_img)
            p2, p98 = np.percentile(_img, (2, 98))
            _img = exposure.rescale_intensity(_img, in_range=(p2, p98))

            _img = color.gray2rgb(_img)
            background += _img * settings['color'] * settings['intensity']

        return exposure.rescale_intensity(background)
