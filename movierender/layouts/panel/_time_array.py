import logging

import matplotlib.pyplot as plt
import numpy as np
import skimage
from fileops.image.exceptions import FrameNotFoundError
from fileops.image.ops import z_projection, rescale
from matplotlib import colors

import movierender.overlays as ovl
from movierender import CompositeRGBImage
from movierender.config import ConfigPanel
from movierender.layouts._ch_config import channel_configuration
from movierender.overlays import PixelTools

logger = logging.getLogger(__name__)


def plotimg(data, panel: ConfigPanel = None, **kwargs):
    imf = panel.image_file
    t = PixelTools(imf)

    ax = plt.gca()

    w_um, h_um = imf.width * imf.um_per_pix, imf.height * imf.um_per_pix
    if panel.scalebar is not None and panel.scalebar > 0:
        sbar = ovl.ScaleBar(ax=ax, um=panel.scalebar, lw=panel.scalebar_thickness,
                            show_text=panel.draw_scalebar_text,
                            xy=t.xy_ratio_to_um(0.05, 0.9), fontdict={'size': panel.fontsize})
    else:
        sbar = None
    tsmp = ovl.Timestamp(ax=ax, xy=t.xy_ratio_to_um(0.02, 0.1),
                         timestamps=panel.image_file.timestamps,
                         string_format=panel.timestamp_format,
                         time_interval=panel.image_file.time_interval,
                         draw_frame=panel.draw_frame_in_timestamp,
                         fontdict={'size': panel.fontsize, 'color': 'white'})
    hst = ovl.ImageHistogram(ax=ax, bins=50, color='white')

    if data["z"].unique().size >= 1 and data["frame"].unique().size == 1 and data["channel"].unique().size == 1:
        _fr = data["frame"].iloc[0]
        _ch = data["channel"].iloc[0]

        try:
            zstack_projection = 'max'
            if np.isreal(_ch):
                img = z_projection(imf, _fr, _ch, z_subset=panel.zstacks, projection=zstack_projection).image
                ch_par = panel.channel_render_parameters[_ch]
                if "overlays" in ch_par and "histogram" in ch_par["overlays"]:
                    # Overlay the histogram on the image plot
                    hst.plot(img)
                # rescale intensities
                img = rescale(img, panel.channel_render_parameters[_ch])
                img = np.stack((img,) * 3, axis=-1) * colors.to_rgb(ch_par["color"])
            elif _ch == "merge":
                crgb = CompositeRGBImage(
                    ax=None,
                    zstack=panel.zstacks,
                    zstack_fn=zstack_projection,
                    channeldict=channel_configuration(panel.channel_render_parameters)
                )
                img = crgb(panel.image_file, frame=_fr)
                img = skimage.util.img_as_float(img)
        except FrameNotFoundError as e:
            ax.set_facecolor('blue')
            return

        ax.imshow(img, cmap='gray', extent=(.0, w_um, h_um, .0),
                  # origin='upper' if self.inv_y else 'lower',
                  origin='upper',
                  interpolation='none', aspect='equal',  # resample=False,
                  zorder=0)

        if sbar is not None:
            sbar.plot()
        tsmp.plot(frame=_fr)

        for ovrl in panel.overlays:
            ovrl.overlay.plot(ax=ax, frame=_fr)

    ax.set_axis_off()
