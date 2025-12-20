from __future__ import annotations

import copy
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import List, TYPE_CHECKING

import imageio.v3 as iio
import moviepy.editor as mpy
import numpy as np
import skimage
from fileops.export.config import ConfigMovie
from fileops.image import ImageFile
from fileops.image.exceptions import FrameNotFoundError
from fileops.pathutils import ensure_dir
from matplotlib.figure import Figure

from movierender.render.pipelines import SingleImage, ImagePipeline, NullImage

if TYPE_CHECKING:
    from movierender.overlays import Overlay

reading_image_lock = threading.Lock()


class SequentialMovieRenderer:
    layers: List[Overlay]
    image: ImageFile

    def __init__(self, fig: Figure, config: ConfigMovie, show_axis=False, invert_y=False, temp_folder=None, **kwargs):
        self._kwargs = {
            'fontdict': {'size': 10},
        }
        self._kwargs.update(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"temp_folder {temp_folder}")
        if temp_folder is None:
            temp_folder = str(uuid.uuid4())

        self.fig = fig
        self.show_axis = show_axis
        self.ax = fig.gca()

        self.layers = []

        self.time = 0
        self.frame = 0
        self.fps = config.fps
        self.duration = None
        self.bitrate = config.bitrate

        imf = config.image_file
        self._cfg = config
        self.image_pipeline: List[ImagePipeline] = []
        self.image = imf
        self.inv_y = invert_y
        self._last_f = imf.frames[-1]
        self._max_frame = max(self._cfg.frames)
        self._frame_offset = min(self._cfg.frames)  # used when frames start at a number greater than zero
        self._render = np.zeros((imf.width, imf.height), dtype=float)
        self._load_image()

        self._tmp = Path(os.curdir) / 'tmp' / 'render' / Path(imf.base_path).name
        if temp_folder:
            self._tmp = self._tmp / temp_folder

    def __iter__(self):
        return self

    def __next__(self):
        if self.image_pipeline is not None:
            imp = self.image_pipeline
        else:
            imp = SingleImage(self)
        self.time = (self.time + 1) % self._max_frame

        return imp(invert_y=self.inv_y)

    def _load_image(self):
        assert len(self.image.frames) > 1, "More than one frame needed to make a movie."
        self.logger.info(f"Loaded {self.image.image_path}. WxH({self.image.width},{self.image.height}), "
                         f"channels: {len(self.image.channels)}, "
                         f"frames: {len(self.image.frames)}, stacks: {len(self.image.zstacks)}")
        self.duration = len(self.image.frames) / self.fps
        self.logger.info(f"Total duration {self.duration:.3f}[s]")

        self._kwargs.update({
            'pix_per_um': self.image.pix_per_um,
            'timestamps': self.image.timestamps,
            'dt':         self.image.time_interval,
            'n_frames':   len(self.image.frames),
            'n_channels': len(self.image.channels),
            'n_zstacks':  len(self.image.zstacks),
            'width':      self.image.width,
            'height':     self.image.height,
            # 'ranges':     self.image.intensity_ranges
        })

    def render(self, filename=None, test=False):
        """
        Render the movie into an mp4 file.
        """

        def make_frame_mpl(t):
            self.time = t
            # calculate frame given time
            _fr_from_t = int(round(self.fps * t)) + self._frame_offset
            self.frame = min(_fr_from_t, self._max_frame)

            if self.frame == self._last_f:
                return self._render

            try:
                self._render = iio.imread(self._tmp.joinpath(f"f{self.frame:05d}.png"))
                self._last_f = self.frame

                # row, col, ch = self._render.shape
                # if ch == 3:
                #     self._render = self._render[:, :, 0:3]
                self._render = self._render[:, :, 0:3]
            except FileNotFoundError:
                self.logger.warning(f"frame {self.frame} not rendered, so using last rendered one")

            # self.logger.debug(f"loaded image of shape {self._render.shape}")
            return self._render

        # Start of method
        if filename is None:
            _, filename = os.path.split(self._file)
            filename += ".mp4"
        rendered_frames = list()
        for fr in sorted(self._cfg.frames):
            try:
                self.render_frame(fr)
                rendered_frames.append(fr)
            except FrameNotFoundError:
                continue

        dur = len(rendered_frames) / self.fps
        animation = mpy.VideoClip(make_frame_mpl, duration=dur)
        animation.write_videofile(filename,
                                  fps=self._cfg.fps,
                                  bitrate=self._cfg.bitrate,
                                  # codec='libx264',
                                  # audio_codec='pcm_s32le',
                                  ffmpeg_params=[
                                      '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
                                      '-pix_fmt', 'yuv420p'
                                  ])
        animation.close()

    def __repr__(self):
        return f"<MovieRender object (sequential) at {hex(id(self))}> with {len(self._kwargs)} arguments."

    def render_frame(self, frame):
        self.logger.info(f"rendering frame {frame}")
        self.frame = frame
        # calculate time given frame
        self.time = (frame - self._frame_offset) / self.fps

        img_path = self._tmp.joinpath(f"f{frame:05d}.png")
        if os.path.exists(img_path):
            self.logger.warning(f'File {img_path.name} already exists in folder {img_path.parent.name}.')
            return

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
                imgp.ax.spines['top'].set_visible(False)
                imgp.ax.spines['right'].set_visible(False)
                imgp.ax.spines['bottom'].set_visible(False)
                imgp.ax.spines['left'].set_visible(False)
        for imgp in self.image_pipeline:
            if type(imgp) == NullImage:
                continue
            ppu = self.image.pix_per_um if self.image.pix_per_um is not None else 1
            ext = (0, self.image.width / ppu, 0, self.image.height / ppu)
            ax = imgp.ax if imgp.ax is not None else self.ax
            with reading_image_lock:
                try:
                    img = imgp()
                    img = skimage.util.img_as_float(img)
                    ax.imshow(img, cmap='gray', extent=ext,
                              origin='upper' if self.inv_y else 'lower',
                              interpolation='none', aspect='equal',
                              zorder=0)
                except TypeError as e:
                    self.logger.error(e)
                except FrameNotFoundError as e:
                    self.logger.error(e)
                    return f"failed to render frame {frame}"
                self.logger.debug(f"frame {frame}: image retrieved OK.")
            for ovrl in self.layers:
                kwargs = self._kwargs.copy()
                kwargs.update(**ovrl._kwargs, show_axis=self.show_axis)
                kwargs.update(show_axis=self.show_axis)
                kwargs.update(**ovrl._kwargs)
                _kwa = copy.copy(kwargs)
                _kwa.pop("timestamps")
                ovrl.plot(ax=self.ax if ovrl.ax is None else None, **kwargs)

        for ovrl in self.layers:
            if not ovrl.show_axis and ovrl.ax is not None:
                ovrl.ax.set_xticklabels([])
                ovrl.ax.set_yticklabels([])
                ovrl.ax.set_xticks([])
                ovrl.ax.set_yticks([])
                ovrl.ax.spines['top'].set_visible(False)
                ovrl.ax.spines['right'].set_visible(False)
                ovrl.ax.spines['bottom'].set_visible(False)
                ovrl.ax.spines['left'].set_visible(False)

        ensure_dir(self._tmp)
        self.fig.savefig(img_path, facecolor='white', transparent=False)
