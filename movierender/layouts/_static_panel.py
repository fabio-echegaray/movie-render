import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import skimage
from fileops.export.config import ConfigPanel
from fileops.image.ops import z_projection
from skimage.exposure import exposure

import movierender.overlays as ovl
from movierender.overlays import PixelTools

logger = logging.getLogger(__name__)


def plotimg(data, panel=None, **kwargs):
    imf = panel.image_file
    t = PixelTools(imf)

    ax = plt.gca()
    ax.cla()

    w_um, h_um = imf.width * imf.um_per_pix, imf.height * imf.um_per_pix
    sbar = ovl.ScaleBar(um=panel.scalebar, lw=3, xy=t.xy_ratio_to_um(0.05, 0.9), fontdict={'size': 9})

    if data["z"].unique().size > 1 and data["frame"].unique().size == 1 and data["channel"].unique().size == 1:
        _fr = data["frame"].iloc[0]
        _ch = data["channel"].iloc[0]
        img = z_projection(imf, _fr, _ch, projection='all-max')

        imgf = skimage.util.img_as_float(img.image)
        if f"channel-{_ch}" in panel.channel_render_parameters:
            ch_par = panel.channel_render_parameters[f"channel-{_ch}"]
            if "overlays" in ch_par and "histogram" in ch_par["overlays"]:
                # Overlay the histogram on the image plot
                axi = ax.inset_axes(
                    (0.5, 0.5, 0.47, 0.47),
                    facecolor='white',
                    frameon=False
                )
                hist, bins = np.histogram(img.image.ravel(), bins=50)
                axi.hist(bins[:-1], bins, weights=hist, histtype='step', color='white', zorder=10)
                # axi.hist(img.ravel(), bins=50, log=False, histtype='step', color='white', zorder=10)
                # axi.set_xlabel('intensity', color='white')
                # axi.set_ylabel('pixel count', color='white')
                axi.tick_params(axis='both', colors='white')
            if "color" in ch_par:
                imgf = exposure.rescale_intensity(imgf, in_range=tuple(np.percentile(imgf, (2, 99))), out_range=(0, 0.85))
                imgf = np.stack((imgf,) * 3, axis=-1) * panel.channel_render_parameters[f"channel-{_ch}"]["color"][1:4]

        ax.imshow(imgf, cmap='gray', extent=(.0, w_um, h_um, .0),
                  # origin='upper' if self.inv_y else 'lower',
                  origin='upper',
                  interpolation='none', aspect='equal',  # resample=False,
                  zorder=0)

        sbar.plot(ax=ax)
    ax.set_axis_off()


def render_static_montage(panel: ConfigPanel,
                          row=None, col=None):
    logger.debug("Making montage of image.")

    # create dataframe of images that will be plotted
    img_lst = [
        {
            'frame':   f,
            'channel': ch,
            'z':       z
        }
        for ch in panel.channels
        for z in panel.zstacks
        for f in panel.frames
    ]
    im_df = pd.DataFrame(img_lst)

    _s = 4.0
    g = sns.FacetGrid(im_df, row=row, col=col, height=_s)
    g = (g.map_dataframe(plotimg, panel=panel)
         .set_titles("{col_name}")
         .add_legend()
         )

    # g.fig.tight_layout()
    plt.subplots_adjust(hspace=0, wspace=0.01, left=0, right=1, top=1, bottom=0)

    g.savefig(panel.filename)
    return g
