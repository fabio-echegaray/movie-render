import datetime
import time as tim

import numpy as np
import pandas as pd
from matplotlib import dates
from movierender.overlays import Overlay


class DataTimeseries(Overlay):
    def __init__(self, df: pd.DataFrame, x="time", y=None, frame="frame", time="time", style_dict=None, **kwargs):
        assert all([it in df.columns for it in [x, y]]), "Data point columns not found in DataFrame."
        self._x = x
        self._y = y
        self._f = frame
        self._t = time
        self._style = style_dict
        self.df = (df
                   .rename(columns={frame: 'frame', time: 'time'})
                   .assign(x=df[x], y=df[y]))

        # assuming 'x' values are time in seconds
        # format seconds to date with this format '%H:%M:%S'
        self.df.loc[:, 'x'] = list(
            map(datetime.datetime.strptime, map(lambda s: tim.strftime('%H:%M:%S', tim.gmtime(s)), self.df['x']),
                len(self.df['x']) * ['%H:%M:%S']))

        super().__init__(**kwargs)

    def plot(self, ax=None, legend=False, plot_dots=True, lw=2, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."
        # assert timestamps is not None, "Need timestamps to render on axes."

        xmin, xmax = self.df['x'].min(), self.df['x'].max()
        ymin, ymax = self.df['y'].min(), self.df['y'].max()
        if not np.isfinite([ymin, ymax]).all():
            return

        fr = self._renderer.frame if self._renderer is not None else self.df['frame'].max()
        dat = self.df.query("frame <= @fr")

        if plot_dots:
            ax.scatter(dat['x'].tolist(), dat['y'], s=1, c='gray', zorder=10)
        for (ix_u, ix_sig), uniseries in self.df.groupby(['unit', 'signal']):
            ax.plot(uniseries['x'], uniseries['y'], c='gray', lw=0.5, zorder=10)
        for (ix_u, ix_sig), uniseries in dat.groupby(['unit', 'signal']):
            color = self._style[ix_sig]['color'] if self._style is not None and 'color' in self._style[ix_sig] else None
            color = color if color is not None else 'r'
            ax.plot(uniseries['x'], uniseries['y'], c=color, lw=lw, zorder=20)

        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])

        formatter = dates.DateFormatter('%H:%M')
        ax.xaxis.set_major_formatter(formatter)
        ax.set_xlabel("Time [hh:mm]")
        ax.xaxis_date()

        if not legend:
            ax.legend([])

    def use_lineplot(self, ax=None, legend=False, **kwargs):
        import seaborn as sns

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
        if not legend:
            ax.get_legend().remove()
