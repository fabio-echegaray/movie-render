import numpy as np
from fileops.image import ImageFile
from fileops.image.imagemeta import MetadataImage
from skimage import exposure

from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class SingleImage(ImagePipeline):
    def __call__(self, *args, channel=0, adjust_exposure=True, **kwargs):

        # check if an ImageFile object is provided as an argument. Use that if provided, otherwise use the renderer.
        if len(args) > 0 and isinstance(args[0], ImageFile):
            imf = args[0]
        elif hasattr(self, "_renderer") and self._renderer is not None:
            imf = self._renderer.image
        else:
            raise ValueError("No image source to render from.")
        # check if frame is provided as an argument. Use that if provided, otherwise use the renderer.
        _frame = kwargs.get("frame", self._renderer.frame if self._renderer is not None else 0)

        ix = imf.ix_at(c=channel, z=self.zstack, t=_frame)
        self.logger.debug(f"Retrieving frame {_frame} of channel {channel} at z-stack={self.zstack} "
                          f"(index={ix})")
        mimg = imf.image(ix)
        img = mimg.image if (type(mimg) is MetadataImage and mimg.image is not None) else (
            np.zeros((imf.width, imf.height)))
        if adjust_exposure:
            p2, p98 = np.percentile(img, (2, 98))
            img = exposure.rescale_intensity(img, in_range=(p2, p98))
        return img
