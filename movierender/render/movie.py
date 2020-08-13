from __future__ import annotations
import os
import logging

import numpy as np
from czifile import CziFile
# import skimage.external.tifffile as tf
import xml.etree.ElementTree

import moviepy.editor as mpy
from moviepy.video.io.bindings import mplfig_to_npimage

from typing import List, TYPE_CHECKING

from movierender.render.pipelines import SingleImage

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
        self._load_image()

    def __iter__(self):
        return self

    def __next__(self):
        channel = zstack = 1
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

        for root, directories, filenames in os.walk(folder):
            for file in filenames:
                joinf = os.path.abspath(os.path.join(root, file))
                if os.path.isfile(joinf) and joinf[-4:] == '.tif' and file == img_name:
                    return self._load_tiff(joinf)
                if os.path.isfile(joinf) and joinf[-4:] == '.czi' and file == img_name:
                    return self._load_zeiss(joinf)

    def _load_tiff(self, path):
        raise Exception('Not yet implemented.')
        # _, img_name = os.path.split(path)
        # with tf.TiffFile(path) as tif:
        #     if tif.is_imagej is not None:
        #         metadata = tif.pages[0].imagej_tags
        #         dt = metadata['finterval'] if 'finterval' in metadata else 1
        #
        #         # asuming square pixels
        #         xr = tif.pages[0].tags['x_resolution'].value
        #         res = float(xr[0]) / float(xr[1])  # pixels per um
        #         if metadata['unit'] == 'centimeter':
        #             res = res / 1e4
        #
        #         images = None
        #         if len(tif.pages) == 1:
        #             if ('slices' in metadata and metadata['slices'] > 1) or (
        #                     'frames' in metadata and metadata['frames'] > 1):
        #                 images = tif.pages[0].asarray()
        #             else:
        #                 images = [tif.pages[0].asarray()]
        #         elif len(tif.pages) > 1:
        #             images = list()
        #             for i, page in enumerate(tif.pages):
        #                 images.append(page.asarray())
        #
        #         return np.array(images), res, dt, \
        #                metadata['frames'] if 'frames' in metadata else 1, \
        #                metadata['channels'] if 'channels' in metadata else 1

    def _load_zeiss(self, path):
        _, img_name = os.path.split(path)
        with CziFile(path) as czi:
            xmltxt = czi.metadata()
            meta = xml.etree.ElementTree.fromstring(xmltxt)

            # next line is somewhat cryptic, but just extracts um/pix (calibration) of X and Y into res
            res = [float(i[0].text) for i in meta.findall('.//Scaling/Items/*') if
                   i.attrib['Id'] == 'X' or i.attrib['Id'] == 'Y']
            assert np.isclose(res[0], res[1]), "Pixels are not square."

            # get first calibration value and convert it from meters to um
            res = res[0] * 1e6

            ts_ix = [k for k, a1 in enumerate(czi.attachment_directory) if a1.filename[:10] == 'TimeStamps'][0]
            timestamps = list(czi.attachments())[ts_ix].data()
            dt = np.median(np.diff(timestamps))

            ax_dct = {n: k for k, n in enumerate(czi.axes)}
            n_frames = czi.shape[ax_dct['T']]
            n_channels = czi.shape[ax_dct['C']]
            n_zstacks = czi.shape[ax_dct['Z']]
            n_x = czi.shape[ax_dct['X']]
            n_y = czi.shape[ax_dct['Y']]
            assert n_frames > 1, "More than one frame needed to make a movie."

            self.images = list()
            for sb in czi.subblock_directory:
                self.images.append(sb.data_segment().data().reshape((n_x, n_y)))

            self.logger.info(f"Loaded {czi._fh.name}. WxH({n_x},{n_y}), channels: {n_channels}, "
                             f"frames: {n_frames}, stacks: {n_zstacks}")

            self._kwargs.update({
                'pix_per_um': 1 / res,
                'timestamps': timestamps - timestamps[0],
                'dt': dt,
                'n_frames': n_frames,
                'n_channels': n_channels,
                'n_zstacks': n_zstacks,
                'width': n_x,
                'height': n_y
            })

    def render(self, filename=None, test=False):
        """
        Builds and displays the movie.
        """

        def make_frame_mpl(t):
            im = self.__next__()

            self.ax.cla()
            ext = [0, self.width / self.pix_per_um, 0, self.height / self.pix_per_um]
            self.ax.imshow(im, extent=ext, cmap='gray', interpolation='none', aspect='equal', origin='lower')

            for ovrl in self.layers:
                kwargs = self._kwargs.copy()
                kwargs.update(**ovrl._kwargs)
                ovrl.plot(self.ax, **kwargs)

            return mplfig_to_npimage(self.ax.get_figure())  # RGB image of the figure

        if filename is None:
            _, filename = os.path.split(self._file)
            filename += ".mp4"

        if test:
            im = make_frame_mpl(0)
            self.ax.axis('on')
            path, img_name = os.path.split(self._file)
            self.ax.get_figure().savefig(os.path.join(path, img_name + ".test.png"))

        animation = mpy.VideoClip(make_frame_mpl, duration=self.n_frames / self.fps)
        animation.write_videofile(filename, fps=self.fps, bitrate=self.bitrate)
        animation.close()

    def __repr__(self):
        return f"<MovieRender object at {hex(id(self))}> with {len(self._kwargs)} arguments."
