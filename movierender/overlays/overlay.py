from movierender.render import MovieRenderer


class Overlay(object):
    def __init__(self, ax=None, **kwargs):
        self.layers = [self]
        self._kwargs = kwargs
        self._renderer: MovieRenderer | None = None
        self.ax = ax

    def __radd__(self, ovrl):
        if isinstance(ovrl, MovieRenderer):
            ovrl.layers += self.layers
            self._renderer = ovrl
            self.show_axis = self._renderer.show_axis
            return ovrl

        self.layers.append(ovrl)
        return self

    def plot(self, ax, **kwargs):
        pass
