import logging

import matplotlib.pyplot as plt
import numpy as np
import skimage
from fileops.image.exceptions import FrameNotFoundError
from matplotlib import colors
from skimage.exposure import exposure

import movierender.overlays as ovl
from layouts._ch_config import channel_configuration
from movierender import CompositeRGBImage
from movierender.config import ConfigPanel
from movierender.overlays import PixelTools

logger = logging.getLogger(__name__)


def plotimg(data, panel: ConfigPanel = None, **kwargs):
    imf = panel.image_file
    t = PixelTools(imf)

    if data["frame"].unique().size != 1:
        raise ValueError("Z-array layout demands only one frame.")
    if data["channel"].unique().size != 1 or data["channel"].unique().size != 1:
        raise RuntimeError("More than one z or channel value to render.")
    if panel.zstack_fn is not None:
        logger.warning(
            f"Discarding 'zstack_fn' parameter (it is set as {panel.zstack_fn}, but it's not used in this render).")

    ax = plt.gca()
    ax.cla()

    _z = data["z"].iloc[0]
    _fr = data["frame"].iloc[0]
    _ch = data["channel"].iloc[0]
    w_um, h_um = imf.width * imf.um_per_pix, imf.height * imf.um_per_pix
    sbar = ovl.ScaleBar(ax=ax, um=panel.scalebar, lw=panel.scalebar_thickness,
                        show_text=panel.draw_scalebar_text,
                        xy=t.xy_ratio_to_um(0.05, 0.9), fontdict={'size': panel.fontsize})
    tsmp = ovl.Timestamp(ax=ax, xy=t.xy_ratio_to_um(0.02, 0.07),
                         timestamps=panel.image_file.timestamps,
                         string_format=panel.timestamp_format,
                         time_interval=panel.image_file.time_interval,
                         draw_frame=panel.draw_frame_in_timestamp,
                         fontdict={'size': panel.fontsize, 'color': 'white'})
    ztxt = ovl.Text(f"z{_z:02d}({_z * imf.um_per_z:0.2f}um)", ax=ax, xy=t.xy_ratio_to_um(0.60, 0.07),
                    fontdict={'size': panel.fontsize, 'color': 'white'})
    hst = ovl.ImageHistogram(ax=ax, bins=50, color='white')

    try:
        if np.isreal(_ch):
            img = imf.image(imf.ix_at(_ch, _z, _fr)).image
        elif _ch == "merge":
            crgb = CompositeRGBImage(
                ax=None,
                zstack=_z,
                zstack_fn=None,
                channeldict=channel_configuration(panel.channel_render_parameters)
            )
            img = crgb(panel.image_file, frame=_fr)
    except FrameNotFoundError as e:
        ax.set_facecolor('blue')
        return

    imgf = skimage.util.img_as_float(img)
    if _ch in panel.channel_render_parameters:
        ch_par = panel.channel_render_parameters[_ch]
        if "overlays" in ch_par and "histogram" in ch_par["overlays"]:
            # Overlay the histogram on the image plot
            hst.plot(img)
        if "color" in ch_par:
            imgf = exposure.rescale_intensity(imgf, in_range=tuple(np.percentile(imgf, (0.1, 99.9))))
            imgf = exposure.adjust_gamma(imgf,
                                         gamma=ch_par['gamma_value'] if 'gamma_value' in ch_par else 1,
                                         gain=ch_par['gamma_gain'] if 'gamma_gain' in ch_par else 1)
            imgf = np.stack((imgf,) * 3, axis=-1) * colors.to_rgb(ch_par["color"])

    ax.imshow(imgf, cmap='gray', extent=(.0, w_um, h_um, .0),
              # origin='upper' if self.inv_y else 'lower',
              origin='upper',
              interpolation='none', aspect='equal',  # resample=False,
              zorder=0)

    sbar.plot()
    tsmp.plot(frame=_fr)
    ztxt.plot(frame=_fr)

    for ovrl in panel.overlays:
        ovrl.overlay.plot(ax=ax, frame=_fr)

    ax.set_axis_off()
