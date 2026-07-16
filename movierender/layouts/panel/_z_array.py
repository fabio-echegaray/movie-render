import logging

import matplotlib.pyplot as plt
import numpy as np
import skimage
from fileops.image.exceptions import FrameNotFoundError
from matplotlib import colors

import movierender.overlays as ovl
from movierender import CompositeRGBImage
from movierender.config import ConfigPanel
from movierender.layouts._ch_config import channel_configuration
from movierender.overlays import PixelTools
from movierender.render.pipelines._image_rescale import rescale

logger = logging.getLogger(__name__)


def plotimg(data, panel: ConfigPanel = None, **kwargs):
    imf = panel.image_file
    t = PixelTools(imf)

    if data["frame"].unique().size != 1:
        raise ValueError("Z-array layout demands only one frame.")
    if data["channel"].unique().size != 1 or data["z"].unique().size != 1:
        raise RuntimeError("More than one z or channel value to render.")
    if panel.zstack_fn is not None:
        logger.warning(
            f"Discarding 'zstack_fn' parameter (it is set as {panel.zstack_fn}, but it's not used in this render).")

    ax = plt.gca()

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
    # z_txt=f"z{_z:02d}({_z * imf.um_per_z:0.2f}um)"
    z_txt = f"z{_z * imf.um_per_z:0.2f}um"
    ztxt = ovl.Text(z_txt, ax=ax, xy=t.xy_ratio_to_um(0.50, 0.07),
                    fontdict={'size': panel.fontsize, 'color': 'white'})
    hst = ovl.ImageHistogram(ax=ax, bins=50, color='white')

    try:
        if np.isreal(_ch):
            img = imf.image(imf.ix_at(_ch, _z, _fr)).image
            ch_par = panel.channel_render_parameters[_ch]
            if "overlays" in ch_par and "histogram" in ch_par["overlays"]:
                # Overlay the histogram on the image plot
                hst.plot(img)
            # rescale intensities
            img = rescale(img, panel.channel_render_parameters[_ch], as_original_dtype=True)
            img = skimage.util.img_as_float(img)
            img = np.stack((img,) * 3, axis=-1) * colors.to_rgb(ch_par["color"])
        elif _ch == "merge":
            crgb = CompositeRGBImage(
                ax=None,
                zstack=int(_z),
                zstack_fn=None,
                channeldict=channel_configuration(panel.channel_render_parameters)
            )
            img = crgb(panel.image_file, frame=_fr)
            img = skimage.util.img_as_float(img)
    except FrameNotFoundError as e:
        ax.set_facecolor('blue')
        return

    # img = exposure.rescale_intensity(img, in_range=tuple(np.percentile(img, (0.1, 99.9))))
    ax.imshow(img, cmap='gray', extent=(.0, w_um, h_um, .0),
              origin='upper',
              interpolation='none', aspect='equal',  # resample=False,
              zorder=0)

    sbar.plot()
    tsmp.plot(frame=_fr)
    ztxt.plot(frame=_fr)

    for ovrl in panel.overlays:
        ovrl.overlay.plot(ax=ax, frame=_fr, ch=_ch, z=_z)

    ax.set_axis_off()
