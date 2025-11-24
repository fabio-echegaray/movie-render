import numpy as np
from fileops.image.imagemeta import MetadataImage
from skimage import exposure

from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class SingleImage(ImagePipeline):
    def __call__(self, *args, channel=0, adjust_exposure=True, **kwargs):
        r = self._renderer

        ix = r.image.ix_at(c=channel, z=self.zstack, t=r.frame)
        self.logger.debug(f"Retrieving frame {r.frame} of channel {channel} at z-stack={self.zstack} "
                          f"(index={ix})")
        mimg = r.image.image(ix)
        img = mimg.image if (type(mimg) is MetadataImage and mimg.image is not None) else np.zeros((r.width, r.height))
        if adjust_exposure:
            p2, p98 = np.percentile(img, (2, 98))
            img = exposure.rescale_intensity(img, in_range=(p2, p98))
        return img
