import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from fileops.export.config import ConfigCopyright
from matplotlib.backends.backend_pdf import PdfPages

from movierender.config import ConfigPanel

logger = logging.getLogger(__name__)


# function to effectively group plots whe making a FacetGrid
def grouper(iterable, n, fillvalue=None):
    from itertools import zip_longest
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def render_static_montage(panel: ConfigPanel, copyright_info: ConfigCopyright = None) -> Path:
    logger.debug("Making montage of image.")

    # create dataframe of images that will be plotted
    img_lst = [
        {
            'frame':   f,
            'channel': ch,
            'z':       z
        }
        for ch in panel.channels + ["merge"]
        for z in panel.zstacks
        for f in panel.frames
    ]
    im_df = pd.DataFrame(img_lst)

    # ------------------------------------------------------------------------------------------------------------------
    # process layout
    # ------------------------------------------------------------------------------------------------------------------
    if panel.layout == "z-array":
        from layouts.panel._z_array import plotimg
        rows = "z"
        cols = "channel"
    elif panel.layout == "time-array":
        from layouts.panel._time_array import plotimg
        rows = "channel"
        cols = "frame"
    else:
        raise ValueError(f"Wrong layout specification (got {panel.layout}).")

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
                for col_g in grouper(g_df[panel.columns].unique(), panel.max_plots_per_page):
                    g = sns.FacetGrid(g_df,
                                      row=rows,
                                      col=cols,
                                      col_wrap=panel.max_columns,
                                      col_order=col_g,
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
                          row=rows,
                          col=cols,
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
