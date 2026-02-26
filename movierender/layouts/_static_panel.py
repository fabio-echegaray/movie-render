import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import skimage
from fileops.export.config import ConfigCopyright
from fileops.image.exceptions import FrameNotFoundError
from fileops.image.ops import z_projection
from matplotlib import colors
from matplotlib.backends.backend_pdf import PdfPages
from skimage.exposure import exposure

import movierender.overlays as ovl
from movierender.config import ConfigPanel
from movierender.overlays import PixelTools

logger = logging.getLogger(__name__)


# function to effectively group plots whe making a FacetGrid
def grouper(iterable, n, fillvalue=None):
    from itertools import zip_longest
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


# core plotting function
def plotimg(data, panel: ConfigPanel = None, **kwargs):
    imf = panel.image_file
    t = PixelTools(imf)

    ax = plt.gca()
    ax.cla()

    w_um, h_um = imf.width * imf.um_per_pix, imf.height * imf.um_per_pix
    sbar = ovl.ScaleBar(ax=ax, um=panel.scalebar, lw=panel.scalebar_thickness,
                        show_text=panel.draw_scalebar_text,
                        xy=t.xy_ratio_to_um(0.05, 0.9), fontdict={'size': panel.fontsize})
    tsmp = ovl.Timestamp(ax=ax, xy=t.xy_ratio_to_um(0.02, 0.1),
                         timestamps=panel.image_file.timestamps,
                         string_format=panel.timestamp_format,
                         time_interval=panel.image_file.time_interval,
                         draw_frame=panel.draw_frame_in_timestamp,
                         fontdict={'size': panel.fontsize, 'color': 'white'})
    hst = ovl.ImageHistogram(ax=ax, bins=50, color='white')

    if data["z"].unique().size > 1 and data["frame"].unique().size == 1 and data["channel"].unique().size == 1:
        _fr = data["frame"].iloc[0]
        _ch = data["channel"].iloc[0]

        # if row['z'] >= 0:
        #     mdi = self.imf.image(self.imf.ix_at(self._channel, row['z'], row['frame']))
        # else:
        #     mdi = self.imf.z_projection(row['frame'], self._channel, projection=ZProjection(row['z']).name)

        try:
            img = z_projection(imf, _fr, _ch, projection='all-max')
        except FrameNotFoundError as e:
            ax.set_facecolor('blue')
            return

        imgf = skimage.util.img_as_float(img.image)
        if _ch in panel.channel_render_parameters:
            ch_par = panel.channel_render_parameters[_ch]
            if "overlays" in ch_par and "histogram" in ch_par["overlays"]:
                # Overlay the histogram on the image plot
                hst.plot(img)
            if "color" in ch_par:
                imgf = exposure.rescale_intensity(imgf, in_range=tuple(np.percentile(imgf, (0.1, 99.9))))
                imgf = exposure.adjust_gamma(imgf, gamma=0.8, gain=2)
                imgf = np.stack((imgf,) * 3, axis=-1) * colors.to_rgb(ch_par["color"])

        ax.imshow(imgf, cmap='gray', extent=(.0, w_um, h_um, .0),
                  # origin='upper' if self.inv_y else 'lower',
                  origin='upper',
                  interpolation='none', aspect='equal',  # resample=False,
                  zorder=0)

        sbar.plot()
        tsmp.plot(frame=_fr)

        for ovrl in panel.overlays:
            ovrl.overlay.plot(ax=ax, frame=_fr)

    ax.set_axis_off()


def render_static_montage(panel: ConfigPanel, copyright_info: ConfigCopyright = None) -> Path:
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

    # ------------------------------------------------------------------------------------------------------------------
    # save a multipage pdf and associated metadata
    # ------------------------------------------------------------------------------------------------------------------
    filepath = panel.configfile.parent / panel.filename
    matplotlib.rc('pdf', fonttype=42, use14corefonts=True)
    metadata = {
        'Title':   panel.title,
        'Subject': panel.description,
        'Author':  copyright_info.author if copyright_info is not None else "unknown author",
        'Creator': 'MovieRender (Python package, https://pypi.org/project/movierender)',
    }
    gs_kwargs = dict(left=0.1,  # Left border of the subplots
                     right=0.95,  # Right border of the subplots
                     top=0.9,  # Top border of the subplots
                     bottom=0.15,  # Bottom border of the subplots
                     wspace=0,  # Horizontal space between subplots
                     hspace=0.01  # Vertical space between subplots
                     )

    if panel.multipage:
        with PdfPages(filepath, metadata=metadata) as pdf:
            for page_lbl, g_df in im_df.groupby(panel.rows):
                for cols in grouper(g_df[panel.columns].unique(), panel.max_plots_per_page):
                    g = sns.FacetGrid(g_df,
                                      row=None,
                                      col=panel.columns,
                                      col_wrap=panel.max_columns,
                                      col_order=cols,
                                      aspect=1,
                                      height=panel.height)
                    g = (g.map_dataframe(plotimg, panel=panel)
                         # .set_titles("{col_name}")
                         .add_legend()
                         )

                    # Remove unused axes
                    for ax in g.axes.flatten():
                        if not ax.has_data():  # Check if the axis has data
                            ax.set_visible(False)  # Hide the axis

                    g.figure.suptitle(f"{panel.title} ({panel.rows} {page_lbl})")
                    plt.subplots_adjust(**gs_kwargs)  # Manually adjust subplot positions
                    pdf.savefig(transparent=True)
    else:
        g = sns.FacetGrid(im_df,
                          row=panel.rows,
                          col=panel.columns,
                          aspect=1,
                          height=panel.height)
        g = (g.map_dataframe(plotimg, panel=panel)
             # .set_titles("{col_name}")
             .add_legend()
             )

        # Remove unused axes
        for ax in g.axes.flat:
            if not ax.has_data():  # Check if the axis has data
                ax.set_visible(False)  # Hide the axis

        g.figure.suptitle(f"{panel.title}")
        plt.subplots_adjust(**gs_kwargs)  # Manually adjust subplot positions

        g.savefig(filepath, metadata=metadata, transparent=True)

    return filepath
