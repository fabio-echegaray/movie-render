from __future__ import annotations
import os
import logging

import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage

from typing import List, TYPE_CHECKING

from movierender.render.pipelines import SingleImage
from ._image import find_image

if TYPE_CHECKING:
    from movierender.overlays import Overlay


class MovieRenderer:
    layers: List[Overlay]

    def __init__(self, fig, file: str, fps=1, bitrate="4000k", show_axis=False, **kwargs):
        self._kwargs = {
            'fontdict': {'size': 10},
            }
        self._kwargs.update(**kwargs)

        self.fig = fig
        if show_axis:
            self.ax = fig.gca()
        else:
            self.ax = fig.add_axes([0, 0, 1, 1])
            self.ax.axis('off')

        self.layers = []
        self.logger = logging.getLogger(__name__)

        self.frame = 0
        self.fps = fps
        self.bitrate = bitrate

        self.image_pipeline = None
        self.images = None
        self._file = file
        self._last_t = None
        self._render = None
        self._load_image()

    def __iter__(self):
        return self

    def __next__(self):
        if self.image_pipeline is not None:
            imp = self.image_pipeline
        else:
            imp = SingleImage(self)
        self.frame = (self.frame + 1) % self.n_frames

        return imp()

    def __getattr__(self, name):
        if name in self._kwargs:
            return self._kwargs[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def _load_image(self):
        folder = os.path.dirname(self._file)
        img_name = os.path.basename(self._file)

        img = find_image(img_name, folder=folder)

        assert img.frames > 1, "More than one frame needed to make a movie."
        self.logger.info(f"Loaded {img_name}. WxH({img.width},{img.height}), channels: {img.channels}, "
                         f"frames: {img.frames}, stacks: {img.zstacks}")

        self.images = img.image

        self._kwargs.update({
            'pix_per_um': img.pix_per_um,
            'timestamps': img.timestamps,
            'dt':         img.time_interval,
            'n_frames':   img.frames,
            'n_channels': img.channels,
            'n_zstacks':  img.zstacks,
            'width':      img.width,
            'height':     img.height
            })

    def render(self, filename=None, test=False):
        """
        Builds and displays the movie.
        """

        def make_frame_mpl(t):
            self.frame = int(round(t))

            if self.frame == self._last_t:
                return self._render

            self.ax.cla()
            ext = [0, self.width / self.pix_per_um, 0, self.height / self.pix_per_um]
            self.ax.imshow(self.image_pipeline(), extent=ext, cmap='gray',
                           interpolation='none', aspect='equal', origin='lower')

            for ovrl in self.layers:
                kwargs = self._kwargs.copy()
                kwargs.update(**ovrl._kwargs)
                ovrl.plot(self.ax, **kwargs)

            self._last_t = self.frame
            self._render = mplfig_to_npimage(self.ax.get_figure())  # RGB image of the figure
            return self._render

        if filename is None:
            _, filename = os.path.split(self._file)
            filename += ".mp4"

        if test:
            im = make_frame_mpl(0)
            self.ax.axis('on')
            path, img_name = os.path.split(self._file)
            self.ax.get_figure().savefig(os.path.join(path, img_name + ".test.png"))

        animation = mpy.VideoClip(make_frame_mpl, duration=self.n_frames - 1)
        animation.write_videofile(filename, fps=self.fps, bitrate=self.bitrate)
        animation.close()

    def __repr__(self):
        return f"<MovieRender object at {hex(id(self))}> with {len(self._kwargs)} arguments."
