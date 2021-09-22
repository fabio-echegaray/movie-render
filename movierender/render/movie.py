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
        self.show_axis = show_axis
        self.ax = fig.gca()

        self.layers = []
        self.logger = logging.getLogger(__name__)

        self.time = 0
        self.fps = fps
        self.duration = None
        self.bitrate = bitrate

        self.image_pipeline = []
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
            for imgp in self.image_pipeline:
                if imgp.ax is not None:
                    imgp.ax.cla()
                if not self.show_axis and imgp.ax is not None:
                    imgp.ax.set_xticklabels([])
                    imgp.ax.set_yticklabels([])
                    imgp.ax.set_xticks([])
                    imgp.ax.set_yticks([])

            for imgp in self.image_pipeline:
                ext = [0, self.width / self.pix_per_um, 0, self.height / self.pix_per_um]
                ax = imgp.ax if imgp.ax is not None else self.ax
                ax.imshow(imgp(), cmap='gray', extent=ext, origin='lower',
                          interpolation='none', aspect='equal',
                          zorder=0)

            for ovrl in self.layers:
                kwargs = self._kwargs.copy()
                kwargs.update(**ovrl._kwargs, show_axis=self.show_axis)
                ovrl.plot(ax=self.ax if ovrl.ax is None else None, **kwargs)

            for ovrl in self.layers:
                if not ovrl.show_axis and ovrl.ax is not None:
                    ovrl.ax.set_xticklabels([])
                    ovrl.ax.set_yticklabels([])
                    ovrl.ax.set_xticks([])
                    ovrl.ax.set_yticks([])
            self.fig.tight_layout()

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
            return

        animation = mpy.VideoClip(make_frame_mpl, duration=self.duration)
        animation.write_videofile(filename, fps=self.fps, bitrate=self.bitrate)
        animation.close()

    def __repr__(self):
        return f"<MovieRender object at {hex(id(self))}> with {len(self._kwargs)} arguments."
