from fileops.image import ImageFile

from movierender.colorize import DEFAULT_DEPTH_CMAP, is_depth_projection, z_depth_rgb
from movierender.render.pipelines._image_pipeline_base import ImagePipeline


class ZProjectionImage(ImagePipeline):
    """Render a z-projection of a *single* channel.

    This is the pipeline that the layouts must use whenever a z-projection is
    requested, and in particular for *depth-coded* projections.


    Usage
    -----
    The pipeline renders the projection defined by ``zstack``/``zstack_fn``
    (see :class:`ImagePipeline`) of the given ``channel`` on demand::

        img = ZProjectionImage(channel=0, zstack=[0, 1, 2, 3],
                               zstack_fn='all-depth', zstack_cmap='plasma')
        rgb = img(image_file, frame=0)      # (H, W, 3) float in [0, 1]
        gray = img(channel=1, frame=0)      # (H, W) for e.g. 'all-max'

    The returned array is the raw projection: an ``(H, W)`` grayscale image for
    ``max``/``min``/``mean``/... projections.  For depth-coding the result is
    an ``(H, W, 3)`` RGB image produced by colourising the depth data through
    ``zstack_cmap`` (see :mod:`movierender.colorize`); because the colours
    must encode position while dark regions stay black, depth colourising
    also reads a parallel max-projection of the same channel for the pixel
    intensity.  No per-channel tint is ever applied here — the caller is
    responsible for colouring a grayscale projection if needed.

    ``zstack_cmap`` chooses the colormap used for the depth-encoding colours;
    its default (``DEFAULT_DEPTH_CMAP``) is the perceptually-uniform
    ``'plasma'``.
    """

    def __call__(self, *args, channel=None, frame=None, **kwargs):
        # Image file: use the one passed as an argument, falling back to the
        # renderer's current image file.
        if len(args) > 0 and isinstance(args[0], ImageFile):
            imf = args[0]
        elif getattr(self, "_renderer", None) is not None:
            imf = self._renderer.image
        else:
            raise ValueError("No image source to render from.")

        # Frame: use the one passed as an argument, falling back to the
        # renderer's current frame.
        if frame is None and getattr(self, "_renderer", None) is not None:
            frame = self._renderer.frame
        _frame = 0 if frame is None else frame

        # Channel: prefer the call-time argument; fall back to the channel
        # passed to the constructor.  The renderer calls ``imgp()`` with
        # no arguments, so without this fallback every depth-coded cell would
        # render channel 0.
        if channel is None:
            channel = self._kwargs.get('channel', 0)

        if isinstance(self.zstack, int) and self.zstack >= 0:
            raise ValueError(
                "ZProjectionImage renders a z-projection across a z-range; "
                f"got a single z-plane (zstack={self.zstack}). "
                "Use SingleImage for a single plane.")

        # parse relevant structures of z_subset (propagating 'all' would make
        # z_volume iterate the characters of the string).
        z_subset = self.zstack if isinstance(self.zstack, (list, set)) else None

        # Depth-coding produces colours that encode z-position: colourising
        # the depth *data* is a presentation concern handled in
        # ``movierender.colorize`` and is not a projection type, so it never
        # reaches FileOps' z_projection.
        if is_depth_projection(self.zstack_fn):
            return z_depth_rgb(imf, frame=_frame, channel=channel, z_subset=z_subset,
                               cmap_name=self.zstack_cmap)

        mdi = imf.z_projection(frame=_frame, channel=channel, z_subset=z_subset,
                               projection=self.zstack_fn)
        return mdi.image