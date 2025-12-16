import numpy as np

from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class NullImage(ImagePipeline):
    def __call__(self, *args, **kwargs):
        nimg = np.zeros((1, 1), dtype=np.uint8)
        return nimg
