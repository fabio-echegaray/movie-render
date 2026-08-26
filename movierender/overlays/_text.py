from .overlay import Overlay, get_kwargs
from movierender.config import TextProperties
from movierender.config._cfg_graphics import resolve_text_color


class Text(Overlay):
    def __init__(self, text, text_props=None, **kwargs):
        if text is None:
            raise ValueError("Need text to render on axes.")
        self.text = text
        self._text_props = text_props if text_props is not None else TextProperties()
        self._kwargs = kwargs
        super().__init__(**kwargs)

    def plot(self, ax=None, xy=None, fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        if ax is None:
            raise RuntimeError("No axes found to plot overlay.")

        def_values = get_kwargs([kwargs, self._kwargs],
                                keys_and_default_values=dict(
                                    fontdict=None,
                                    va='center',
                                    color='white',
                                    alpha=1.0,
                                    zorder=1,
                                    frame=self._renderer.frame if self._renderer is not None else None)
                                )
        fontdict, va, color, alpha, zorder, frame = def_values

        if xy is None:
            xy = self._kwargs["xy"] if "xy" in self._kwargs else None

        x0, y0 = xy
        bg_color = ax.get_figure().get_facecolor()
        _fontdict = dict(fontdict) if fontdict else {}
        _fontdict.setdefault('size', self._text_props.font_size)
        _fontdict.setdefault('family', self._text_props.font_name)
        _fontdict.setdefault('color', resolve_text_color(self._text_props.color, bg_color))
        if self._text_props.font_weight:
            _fontdict.setdefault('weight', self._text_props.font_weight)
        ax.text(x0, y0, self.text,
                fontdict=_fontdict,
                verticalalignment=va, zorder=zorder)
