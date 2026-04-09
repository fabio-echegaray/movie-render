from fileops.plugins.base_plugin import BaseFileOpsPlugin

from movierender.overlays import Overlay


class OverlayPlugin(BaseFileOpsPlugin):
    _ovl: Overlay

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._args = args
        self._kwargs = kwargs

    @property
    def overlay(self):
        return self._clz(*self._args, **self._kwargs)

    @property
    def configuration(self):
        return {'args': self._args, 'kwargs': self._kwargs}
