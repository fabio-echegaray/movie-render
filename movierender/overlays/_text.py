from .overlay import Overlay


class Text(Overlay):
    def __init__(self, text, **kwargs):
        assert text is not None, "Need text to render on axes."
        self.text = text
        super().__init__(**kwargs)

    def plot(self, ax=None, xy=(0, 0), fontdict=None, **kwargs):
        if ax is None:
            ax = self.ax
        assert ax is not None, "No axes found to plot overlay."

        x0, y0 = xy
        ax.text(x0, y0, self.text, color='w', fontdict=fontdict)
