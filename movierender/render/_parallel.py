from __future__ import annotations

import asyncio
import io
import logging
import os
import pickle
from pathlib import Path
from typing import List, TYPE_CHECKING

import asyncpool
import imageio
import matplotlib.pyplot as plt
import moviepy.editor as mpy
import numpy as np
from matplotlib.figure import Figure
# from memory_profiler import profile
from moviepy.video.io.bindings import mplfig_to_npimage

from fileops.image import ImageFile
from fileops.image.exceptions import FrameNotFoundError
from fileops.pathutils import ensure_dir
from movierender.render.pipelines import SingleImage, ImagePipeline

if TYPE_CHECKING:
    from movierender.overlays import Overlay


class ParallelMovieRenderer:
    layers: List[Overlay]
    image: ImageFile

    def __init__(self, fig: Figure, image: ImageFile, fps=1, bitrate="4000k", show_axis=False, invert_y=False,
                 **kwargs):
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
        self.frame = 0
        self.fps = fps
        self.duration = None
        self.bitrate = bitrate

        self.image_pipeline: List[ImagePipeline] = []
        self.image = image
        self.inv_y = invert_y
        self._last_f = image.frames[-1]
        self._render = np.zeros((image.width, image.height), dtype=float)
        self._load_image()

        self._tmp = Path(os.curdir) / 'tmp' / 'render' / Path(image.base_path).name
        ensure_dir(self._tmp)

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

    def __deepcopy__(self):
        # check there is only one figure to render
        figures = {self.fig}
        for imgp in self.image_pipeline:
            if imgp.ax is not None:
                figures.add(imgp.ax.get_figure())
        assert len(
            figures) == 1, "There are more than one figure in this MovieRenderer object and thus cannot be deep-copied."

        # copy new figure and axes from initial instance setup
        buf = io.BytesIO()
        pickle.dump(self.fig, buf)
        buf.seek(0)
        new_fig = pickle.load(buf)

        # extract equivalences between axes
        newax = {old_ax: new_ax for old_ax, new_ax in zip(self.fig.axes, new_fig.axes)}
        # create new MovieRenderer instance
        new_mvr = MovieRenderer(new_fig, self.image, fps=self.fps, bitrate=self.bitrate, show_axis=self.show_axis)
        # copy all image pipelines
        for imgp in self.image_pipeline:
            c_imgp = imgp.__class__
            new_ax = newax[imgp.ax] if imgp.ax is not None else None
            new_imgp = c_imgp(ax=new_ax)
            for d in imgp.__dict__:
                if d not in ['uuid', 'ax', '_renderer']:
                    new_imgp.__dict__.update({d: imgp.__dict__[d]})
            new_imgp.__dict__.update({'_renderer': new_mvr})

            new_mvr.image_pipeline.append(new_imgp)

        # copy all layer render
        for layer in self.layers:
            lcls = layer.__class__
            new_ax = newax[imgp.ax] if imgp.ax is not None else None
            nl = lcls(ax=new_ax)
            for d in layer.__dict__:
                if d not in ['uuid', 'ax', '_renderer']:
                    nl.__dict__.update({d: layer.__dict__[d]})
            nl.__dict__.update({'_renderer': new_mvr})

            new_mvr.layers.append(nl)

        return new_mvr

    def _mem_clean(self):
        self._renderer = None
        self.image_pipeline = None
        self.fig = None
        self.ax = None
        self.layers = None
        self.logger = None
        self.image_pipeline = None
        self.image = None
        self._last_f = None
        self._render = None
        self._tmp = None

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

    def render(self, filename=None):
        """
        Render frames of a movie in parallel.
        """

        def make_frame_mpl(t):
            self.time = t
            # calculate frame given time
            self.frame = int(round(self.fps * t))

            if self.frame == self._last_f:
                return self._render

            self._last_f = self.frame
            self._render = imageio.imread(self._tmp.joinpath(f"f{self.frame:05d}.png"))
            # self.logger.debug(f"loaded image of shape {self._render.shape}")
            return self._render

        # @profile
        async def render_frame(frame, rq):
            img_path = self._tmp.joinpath(f"f{frame:05d}.png")
            if os.path.exists(img_path):
                self.logger.warning(f"skipping frame {frame}.")
                return

            # make a copy of this instance so it can run in parallel
            mvr = self.__deepcopy__()

            mvr.frame = frame

            # clear axes of all objects
            mvr.ax.cla()
            for ovrl in mvr.layers:
                if ovrl.ax is not None:
                    ovrl.ax.cla()
            for imgp in mvr.image_pipeline:
                if imgp.ax is not None:
                    imgp.ax.cla()
                if not mvr.show_axis and imgp.ax is not None:
                    imgp.ax.set_xticklabels([])
                    imgp.ax.set_yticklabels([])
                    imgp.ax.set_xticks([])
                    imgp.ax.set_yticks([])

            for imgp in mvr.image_pipeline:
                try:
                    ppu = mvr.pix_per_um if mvr.pix_per_um is not None else 1
                    ext = [0, mvr.width / ppu, 0, mvr.height / ppu]
                    ax = imgp.ax if imgp.ax is not None else mvr.ax
                    ax.imshow(imgp(), cmap='gray', extent=ext,
                              origin='upper' if self.inv_y else 'lower',
                              interpolation='none', aspect='equal',
                              zorder=0)
                except FrameNotFoundError:
                    continue

            for ovrl in mvr.layers:
                kwargs = mvr._kwargs.copy()
                kwargs.update(**ovrl._kwargs, show_axis=mvr.show_axis)
                ovrl.plot(ax=mvr.ax if ovrl.ax is None else None, **kwargs)

            for ovrl in mvr.layers:
                if not ovrl.show_axis and ovrl.ax is not None:
                    ovrl.ax.set_xticklabels([])
                    ovrl.ax.set_yticklabels([])
                    ovrl.ax.set_xticks([])
                    ovrl.ax.set_yticks([])
            mvr.fig.tight_layout()

            img = mplfig_to_npimage(mvr.fig)  # RGB image of the figure
            imageio.imwrite(img_path, img)

            plt.close(mvr.fig)
            mvr._mem_clean()
            del mvr

            await rq.put(f"Frame {frame} saved to {img_path}.")

        async def result_reader(queue):
            while True:
                value = await queue.get()
                if value is None:
                    break
                self.logger.debug("Got value! -> {}".format(value))

        async def run():
            result_queue = asyncio.Queue()
            reader_future = asyncio.ensure_future(result_reader(result_queue), loop=loop)
            num_procs = os.cpu_count() * 2

            # Start a worker pool with num_procs coroutines, invokes `render_frame` and waits for it to complete.
            async with asyncpool.AsyncPool(loop, num_workers=num_procs,
                                           name="RenderPool",
                                           logger=logging.getLogger("RenderPool"),
                                           worker_co=render_frame,
                                           log_every_n=10) as pool:
                for i in self.image.frames:
                    await pool.push(i, result_queue)

            await result_queue.put(None)
            await reader_future

        # Start of video render method
        if filename is None:
            _, filename = os.path.split(self._file)
            filename += ".mp4"

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())

        animation = mpy.VideoClip(make_frame_mpl, duration=self.duration)
        animation.write_videofile(filename, fps=self.fps, bitrate=self.bitrate)
        animation.close()

    def __repr__(self):
        return f"<MovieRender object at {hex(id(self))}> with {len(self._kwargs)} arguments."
