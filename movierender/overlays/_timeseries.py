import pandas as pd
import seaborn as sns
from movierender.overlays import Overlay


class DataTimeseries(Overlay):
    def __init__(self, df: pd.DataFrame, x="time", y=None, frame="frame", time="time", style=None, hue=None, size=None,
                 **kwargs):
        assert all([it in df.columns for it in [x, y]]), "Data point columns not found in DataFrame."
        self._x = x
        self._y = y
        self._f = frame
        self._t = time
        self.df = (df
                   .rename(columns={frame: 'frame', time: 'time'})
                   .assign(x=df[x], y=df[y]))
        super().__init__(**kwargs)

    def plot(self, ax=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."
        # assert timestamps is not None, "Need timestamps to render on axes."

        xmin, xmax = self.df['x'].min(), self.df['x'].max()
        ymin, ymax = self.df['y'].min(), self.df['y'].max()
        fr = self._renderer.frame
        dat = self.df.query("frame <= @fr")
        ax.scatter(data=dat, x='x', y='y', s=5, c='gray', zorder=10)
        sns.lineplot(data=dat, x='x', y='y',
                     style='variable', hue='signal',
                     units='unit', estimator=None,
                     legend='brief',
                     ax=ax, zorder=20)

        ax.set_xlabel(self._t)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])
        # ax.get_legend().remove()
