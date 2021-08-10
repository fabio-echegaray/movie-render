from __future__ import annotations
import os
import logging

import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage

from typing import List, TYPE_CHECKING

from movierender.render.pipelines import SingleImage
from cached import CachedImageFile

if TYPE_CHECKING:
    from movierender.overlays import Overlay


class MovieRenderer:
    layers: List[Overlay]

    def __init__(self, fig, image: CachedImageFile, fps=1, bitrate="4000k", show_axis=False, **kwargs):
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

        self.time = 0
        self.fps = fps
        self.duration = None
        self.bitrate = bitrate

        self.image_pipeline = None
        self.image = image
        self._last_f = image.frames[-1]
        self._render = None
        self._load_image()

    def __iter__(self):
        return self

    def __next__(self):
        if self.image_pipeline is not None:
            imp = self.image_pipeline
        else:
            imp = SingleImage(self)
        self.time = (self.time + 1) % self.n_frames

        return imp()

    def __getattr__(self, name):
        if name in self._kwargs:
            return self._kwargs[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def _load_image(self):
        assert len(self.image.frames) > 1, "More than one frame needed to make a movie."
        self.logger.info(f"Loaded {self.image.image_path}. WxH({self.image.width},{self.image.height}), "
                         f"channels: {len(self.image.channels)}, "
                         f"frames: {len(self.image.frames)}, stacks: {len(self.image.stacks)}")
        self.duration = len(self.image.frames) / self.fps
        self.logger.info(f"Total duration {self.duration:.3f}[s]")

        self._kwargs.update({
            'pix_per_um': self.image.pix_per_um,
            'timestamps': self.image.timestamps,
            'dt':         self.image.time_interval,
            'n_frames':   len(self.image.frames),
            'n_channels': len(self.image.channels),
            'n_zstacks':  len(self.image.stacks),
            'width':      self.image.width,
            'height':     self.image.height,
            # 'ranges':     self.image.intensity_ranges
        })

    def render(self, filename=None, test=False):
        """
        Builds and displays the movie.
        """

        def make_frame_mpl(t):
            self.time = t
            # calculate frame given time
            self.frame = int(round(self.fps * t) + 1)

            if self.frame == self._last_f:
                return self._render

            # clear axes of all objects
            self.ax.cla()
            for ovrl in self.layers:
                if ovrl.ax is not None:
                    ovrl.ax.cla()
            if self.image_pipeline is not None and self.image_pipeline.ax is not None:
                self.image_pipeline.ax.cla()

            if self.image_pipeline is not None:
                ext = [0, self.width / self.pix_per_um, 0, self.height / self.pix_per_um]
                ax = self.image_pipeline.ax if self.image_pipeline.ax is not None else self.ax
                ax.imshow(self.image_pipeline(), extent=ext, cmap='gray',
                          interpolation='none', aspect='equal', origin='lower', zorder=0)

            for ovrl in self.layers:
                kwargs = self._kwargs.copy()
                kwargs.update(**ovrl._kwargs)
                ovrl.plot(ax=self.ax if ovrl.ax is None else None, **kwargs)

            self._last_f = self.frame
            self._render = mplfig_to_npimage(self.ax.get_figure())  # RGB image of the figure
            return self._render

        # Start of method
        if filename is None:
            _, filename = os.path.split(self._file)
            filename += ".mp4"

        if test:
            im = make_frame_mpl(0)
            self.ax.axis('on')
            path, img_name = os.path.split(filename)
            self.ax.get_figure().savefig(os.path.join(path, img_name + ".test.png"))

        animation = mpy.VideoClip(make_frame_mpl, duration=self.duration)
        animation.write_videofile(filename, fps=self.fps, bitrate=self.bitrate)
        animation.close()

    def __repr__(self):
        return f"<MovieRender object at {hex(id(self))}> with {len(self._kwargs)} arguments."
