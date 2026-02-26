import logging

from movierender.render.pipelines import PipelineException


class ImagePipeline:
    def __init__(self, *args, ax=None, zstack=0, **kwargs):
        self._kwargs = kwargs
        self.ax = ax
        self.zstack = zstack
        self.logger = logging.getLogger(__name__)

        # if len(args) > 0 and isinstance(args[0], MovieRenderer):
        if len(args) > 0 and args[0].__class__.__name__[-13:] == 'MovieRenderer':
            self._renderer = args[0]
        else:
            self._renderer = None

    def __radd__(self, ovrl):
        # if isinstance(ovrl, MovieRenderer):
        if ovrl.__class__.__name__[-13:] == 'MovieRenderer':
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
