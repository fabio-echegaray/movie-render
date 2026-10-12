import logging

import matplotlib.pyplot as plt
import skimage
from fileops.image.exceptions import FrameNotFoundError

import movierender.overlays as ovl
from movierender import CompositeRGBImage
from movierender.config import ConfigPanel
from movierender.config import TextProperties, LineProperties
from movierender.layouts._ch_config import channel_configuration
from movierender.overlays import PixelTools
from movierender.overlays.pixel_tools import crop_extent, roi_pixel_box

logger = logging.getLogger(__name__)


def plotimg(data, panel: ConfigPanel = None, **kwargs):
    imf = panel.image_file
    roi = panel.roi
    t = PixelTools(imf, roi=roi)

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

    # Get graphics parameters from config or use defaults
    sbar_text = panel.scalebar_text or TextProperties(font_size=12)
    sbar_line = panel.scalebar_line or LineProperties(color='white', width=1)
    tsmp_text = panel.timestamp or TextProperties(font_size=12)

    if panel.scalebar is not None and panel.scalebar > 0:
        sbar = ovl.ScaleBar(ax=ax, um=panel.scalebar, lw=panel.scalebar_thickness,
                            show_text=panel.draw_scalebar_text,
                            xy=t.xy_ratio_to_um(0.05, 0.9),
                            text_props=sbar_text, line_props=sbar_line,
                            fontdict={'size': sbar_text.font_size})
    else:
        sbar = None

    tsmp = ovl.Timestamp(ax=ax, xy=t.xy_ratio_to_um(0.02, 0.07),
                         timestamps=panel.image_file.timestamps,
                         string_format=panel.timestamp_format,
                         time_interval=panel.image_file.time_interval,
                         draw_frame=panel.draw_frame_in_timestamp,
                         text_props=tsmp_text)

    # z_txt=f"z{_z:02d}({_z * imf.um_per_z:0.2f}um)"
    z_txt = f"z{_z * imf.um_per_z:0.2f}um"
    ztxt = ovl.Text(z_txt, ax=ax, xy=t.xy_ratio_to_um(0.50, 0.07),
                    text_props=sbar_text,
                    fontdict={'size': sbar_text.font_size, 'color': sbar_text.color})

    hst = ovl.ImageHistogram(ax=ax, bins=50)

    try:
        if _ch != "merge":
            ch_par = panel.channel_render_parameters[_ch]
            ch_name = ch_par["name"]
            ch_cfg = channel_configuration({_ch: ch_par})
            crgb = CompositeRGBImage(
                ax=None,
                zstack=_z,
                channeldict=ch_cfg
            )
            if ("histogram" in ch_par and str(ch_par["histogram"]).lower() in ["yes", "true", "1"]) or \
                    ("overlays" in ch_par and "histogram" in ch_par["overlays"]):
                # Overlay the histogram on the image plot
                imfz = imf.image(imf.ix_at(_ch, _z, _fr))
                hst.plot(imfz.image, channel_params=ch_cfg[ch_name])

            img = crgb(panel.image_file, frame=_fr)
            img = skimage.util.img_as_float(img)
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

    disp = img
    ext = (0.0, w_um, h_um, 0.0)
    if roi is not None:
        y0, y1, x0, x1 = roi_pixel_box(roi, img.shape)
        disp = img[y0:y1, x0:x1]
        ext = crop_extent(ext, roi, img.shape, 'upper')
    ax.imshow(disp, cmap='gray', extent=ext,
              origin='upper',
              interpolation='none', aspect='equal',  # resample=False,
              zorder=0)

    if sbar is not None:
        sbar.plot()
    tsmp.plot(frame=_fr)
    ztxt.plot(frame=_fr)

    for ovrl in panel.overlays:
        ovrl.overlay.plot(ax=ax, frame=_fr, ch=_ch, z=_z)

    ax.set_axis_off()
