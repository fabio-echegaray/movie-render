from movierender.overlays import Overlay


class ScaleBar(Overlay):
    def plot(self, ax=None, um=10, pix_per_um=1, xy=(0, 0), lw=1, fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        x0, y0 = xy
        ax.plot([x0, x0 + um], [y0, y0], c='w', lw=lw)
        ax.text(x0 + um / 2, y0 + 1, f'{um} um', color='w', fontdict=fontdict, horizontalalignment='center')


class Timestamp(Overlay):
    def plot(self, ax=None, xy=(0, 0), string_format="hh:mm", timestamps=None, fontdict=None, va=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."
        assert timestamps is not None, "Need timestamps to render on axes."

        x0, y0 = xy
        secs = timestamps[self._renderer.frame - 1] if len(timestamps) >= self._renderer.frame else timestamps[-1]
        if string_format == "hh:mm":
            mins = int(secs / 60)
            hours = int(mins / 60)
            mins -= hours * 60
            txt = f'{hours:02d}:{mins:02d}'
        elif string_format == "mm:ss":
            mins = int(secs / 60)
            secs -= mins * 60
            if mins < 60:
                txt = f'{mins:02d}:{int(secs):02d}'
            else:
                hours = int(mins / 60)
                mins -= hours * 60
                txt = f'{hours:02d}:{mins:02d}:{int(secs):02d}'
        else:
            raise Exception("Timestamp string format not implemented.")

        txt = f'{self._renderer.frame}  {txt}'
        ax.text(x0, y0, txt, color='w', fontdict=fontdict, verticalalignment=va)
