import matplotlib.colors as mcolors
import numpy as np
from skimage import color, exposure

from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class CompositeRGBImage(ImagePipeline):
    def _img(self, channel):
        r = self._renderer

        if type(self.zstack) is int:
            ix = r.image.ix_at(c=channel, z=self.zstack, t=r.frame)
            self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={self.zstack} "
                              f"(index={ix})")
            return r.image.image(ix).image
        elif type(self.zstack) is str:
            if self.zstack == "all-max":  # max projection
                self.logger.debug(f"Retrieving max z projection of frame {r.frame} and channel {channel}")
                return r.image.z_projection(frame=r.frame, channel=channel).image

    def __call__(self, *args, **kwargs):
        if 'channeldict' not in self._kwargs:
            raise Exception("Channel parameters needed to apply this pipeline.")
        channeldict = self._kwargs['channeldict']

        r = self._renderer

        dtype = None
        background = np.zeros((r.image.height, r.image.width) + (3,), dtype=np.float64)
        for name, settings in channeldict.items():
            channel = settings['id']
            _img = self._img(channel)
            if dtype is None:
                dtype = _img.dtype

            # Contrast enhancing by stretching the histogram
            if 'rescale' in settings and settings['rescale']:
                if type(settings['rescale']) is dict:
                    mini, maxi = settings['rescale']['range']
                    _img = exposure.rescale_intensity(_img, in_range=(mini, maxi))
                elif type(settings['rescale']) is bool and settings['rescale']:
                    _img = exposure.rescale_intensity(_img, in_range=tuple(np.percentile(_img, (0.1, 99.9))))

            _img = color.gray2rgb(_img)
            rgb_vector_color = mcolors.to_rgb(settings['color'])
            assert isinstance(rgb_vector_color, tuple)
            background += _img * rgb_vector_color * settings['intensity']

        return background.astype(dtype)
