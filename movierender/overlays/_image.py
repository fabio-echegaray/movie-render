from movierender.overlays import Overlay


class ScaleBar(Overlay):
    def plot(self, ax, um=10, pix_per_um=1, xy=(0, 0), lw=1, fontdict=None, **kwargs):
        x0, y0 = xy
        ax.plot([x0, x0 + um], [y0, y0], c='w', lw=lw)
        ax.text(x0 + um / 2, y0 + 1, f'{um} um', color='w', fontdict=fontdict, horizontalalignment='center')


class Timestamp(Overlay):
    def plot(self, ax, xy=(0, 0), string_format="hh:mm", timestamps=None, fontdict=None, va=None, **kwargs):
        assert timestamps is not None, "Need timestamps to render on axes."
        x0, y0 = xy
        # secs = sum(timestamps[:self._renderer.frame])
        secs = timestamps[self._renderer.frame]
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
