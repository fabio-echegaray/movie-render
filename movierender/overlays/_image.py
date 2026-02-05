from fileops import get_logger

from .overlay import Overlay, get_kwargs


class ScaleBar(Overlay):
    log = get_logger("ScaleBar(Overlay)")

    def plot(self, ax=None, lw=None, fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        def_values = get_kwargs([kwargs, self._kwargs],
                                keys_and_default_values=dict(
                                    xy=(0, 0),
                                    um=None,
                                    scalebar_length=None,
                                    thickness=1,
                                    lw=1,
                                    alpha=1.0,
                                    zorder=1,
                                    show_text=True,
                                    fontdict=None)
                                )
        xy, um, scalebar_length, thickness, lw, alpha, zorder, show_text, fontdict = def_values

        if um is None and scalebar_length is None:
            self.log.warning("no scalebar length when trying to plot their overlay.")
            return

        lw = max(lw, thickness)
        x0, y0 = xy

        ax.plot([x0, x0 + um], [y0, y0], c='w', lw=lw, zorder=1000)
        if show_text:
            # Add text below the scalebar
            sbar_lw2_um = 352.77778 * lw / 100 / 2
            ax.text(x0 + um / 2, y0 + sbar_lw2_um, f'{um} um', color='w', fontdict=fontdict,
                    horizontalalignment='center', zorder=1000)


def secs_to_string(secs: int, string_format="hh:mm:ss"):
    mins = int(secs / 60)
    hours = int(mins / 60)
    mins -= hours * 60
    secs -= hours * 3600 + mins * 60

    if string_format == "hh:mm:ss":
        txt = f'{hours:02d}:{mins:02d}:{int(secs):02d}'
    elif string_format == "hh:mm":
        txt = f'{hours:02d}:{mins:02d}'
    elif string_format == "mm:ss":
        if hours <= 0:
            txt = f'{mins:02d}:{secs:02d}'
        else:
            txt = f'{hours:02d}:{mins:02d}:{secs:02d}'
    else:
        raise Exception("Timestamp string format not implemented.")

    return txt


class Timestamp(Overlay):
    log = get_logger("Timestamp(Overlay)")

    def plot(self, ax=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        def_values = get_kwargs([kwargs, self._kwargs],
                                keys_and_default_values=dict(
                                    xy=(0, 0),
                                    string_format='hh:mm:ss',
                                    timestamps=None,
                                    draw_frame=True,
                                    time_interval=self._renderer.image.time_interval if self._renderer is not None else 10 ** -6,
                                    fontdict=None,
                                    va='center',
                                    color='white',
                                    alpha=1.0,
                                    zorder=1,
                                    frame=self._renderer.frame if self._renderer is not None else None)
                                )
        xy, string_format, timestamps, draw_frame, time_interval, fontdict, va, color, alpha, zorder, frame = def_values

        if frame is None or timestamps is None:
            self.log.warning("incomplete time information was given when trying to plot their overlay.")
            return

        x0, y0 = xy
        _secs0 = timestamps[frame - 1] if len(timestamps) >= frame else timestamps[-1]
        _secs1 = (frame - 1) * time_interval

        secs = int(max(_secs0, _secs1))
        txt = secs_to_string(secs, string_format)

        txt = f'{frame}  {txt}' if draw_frame else txt
        ax.text(x0, y0, txt, color=color, fontdict=fontdict, verticalalignment=va, zorder=zorder)
