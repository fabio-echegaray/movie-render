import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap

from .overlay import Overlay


class Position(Overlay):
    def __init__(self, df: pd.DataFrame, x="x", y="y", frame="frame", style_dict=None, **kwargs):
        assert all([it in df.columns for it in [x, y, frame]]), "Data point columns not found in DataFrame."
        self._x = x
        self._y = y
        self._f = frame
        self._style = style_dict
        # Rename columns if parameters were given
        self.df = (df
                   .rename(columns={frame: 'frame'})
                   .sort_values(by='frame')
                   .assign(x=df[x], y=df[y]))

        # if self._renderer.inv_y:
        #     self.df["y"]=

        super().__init__(**kwargs)

    def plot(self, ax=None, legend=False, lw=2, tail_length=10, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."
        # assert timestamps is not None, "Need timestamps to render on axis."

        # xmin, xmax = self.df[self._x].min(), self.df[self._x].max()
        ymin, ymax = self.df[self._y].min(), self.df[self._y].max()
        if not np.isfinite([ymin, ymax]).all():
            return

        segments = list()
        fr = self._renderer.frame if self._renderer is not None else self.df[self._f].max()
        fr_min = max(0,fr-tail_length)
        for tid, past in self.df.query("@fr_min < frame <= @fr").groupby('track_id'):
            # ax.plot(past[self._x].tolist()[:tail_length], past[self._y].tolist()[:tail_length], c='yellow', lw=0.5, zorder=1000)
            segments.append([(x, y) for x, y in zip(past[self._x], past[self._y])])
        # Create a colormap that incorporates the alpha values
        alphas = np.linspace(1, 0.2, num=tail_length)
        cmap = LinearSegmentedColormap.from_list("fading_cmap", [(1, 1, 0, a) for a in alphas])
        # Create a LineCollection
        lc = LineCollection(segments, cmap=cmap, linewidth=1)
        lc.set_array(np.arange(len(segments)))  # Assign a value for each segment to map to the colormap
        ax.add_collection(lc)

        dat = self.df.query("frame == @fr")
        if dat.size == 0:
            return
        ax.scatter(dat[self._x].tolist(), dat[self._y].tolist(), s=20, c='blue', zorder=1000)
