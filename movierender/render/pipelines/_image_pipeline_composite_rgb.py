import matplotlib.colors as mcolors
import numpy as np
from fileops.image.ops import ZProjection
from skimage import color, exposure

from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class CompositeRGBImage(ImagePipeline):
    def _img(self, channel):
        r = self._renderer

        if type(self.zstack) is int and self.zstack >= 0:
            ix = r.image.ix_at(c=channel, z=self.zstack, t=r.frame)
            self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={self.zstack} "
                              f"(index={ix})")
            mdi = r.image.image(ix)
            return mdi.image if mdi is not None else None
        elif type(self.zstack) is str or self.zstack < 0:
            if self.zstack.split("-")[1] in ["max", "min", "sum", "std", "avg", "mean", "median", ]:  # max projection
                self.logger.debug(f"Retrieving max z projection of frame {r.frame} and channel {channel}")
                mdi = r.image.z_projection(frame=r.frame, channel=channel, projection=self.zstack)
                return mdi.image if mdi is not None else None
            elif type(self.zstack) is int:
                self.logger.debug(f"Retrieving max z projection of frame {r.frame} and channel {channel}")
                mdi = r.image.z_projection(frame=r.frame, channel=channel, projection=ZProjection(self.zstack).name)
                return mdi.image if mdi is not None else None
        return None

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
            if _img is None:
                continue
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
