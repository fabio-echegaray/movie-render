from .overlay import Overlay, get_kwargs


class Text(Overlay):
    def __init__(self, text, **kwargs):
        assert text is not None, "Need text to render on axes."
        self.text = text
        self._kwargs = kwargs
        super().__init__(**kwargs)

    def plot(self, ax=None, xy=None, fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

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
        ax.text(x0, y0, self.text, color=color, fontdict=fontdict, verticalalignment=va, zorder=zorder)
