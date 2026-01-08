from collections.abc import Iterable

import numpy as np

from movierender.render import MovieRenderer


def iterable_elems_eq(l1: Iterable, l2: Iterable) -> bool:
    if len(l1) != len(l2) or type(l1) != type(l2):
        return False

    for v1 in l1:
        if type(v1) in [int, float, bool, str]:
            v1_in_l2 = np.any([v1 == v2 for v2 in l2])
            if not v1_in_l2:
                return False
        elif type(v1) is dict:
            v1_in_l2 = np.any([dict_elems_eq(v1, v2) for v2 in l2])
            if not v1_in_l2:
                return False
        elif type(v1) is list:
            v1_in_l2 = np.any([dict_elems_eq(v1, v2) for v2 in l2])
            if not v1_in_l2:
                return False
        else:
            raise ValueError

    return True


def dict_elems_eq(d1: dict, d2: dict) -> bool:
    if len(d1) != len(d2) or type(d1) != type(d2):
        return False
    for k1, v1 in d1.items():
        if k1 not in d2:
            return False
        if type(v1) in [int, float, bool, str] or np.isscalar(v1) or v1 is None:
            if v1 != d2[k1]:
                return False
        elif type(v1) is dict:
            dict_eq = dict_elems_eq(v1, d2[k1])
            if not dict_eq:
                return False
        elif isinstance(v1, Iterable):
            lst_eq = iterable_elems_eq(v1, d2[k1])
            if not lst_eq:
                return False
        else:
            raise ValueError

    return True


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
        elif isinstance(ovrl, Overlay):
            self.layers.append(ovrl)
        return self

    def __eq__(self, other: 'Overlay'):
        """ two overlays are equal if their configurations are the same """
        cfg1 = self.configuration
        cfg2 = other.configuration
        cfg1.pop("layers")
        cfg2.pop("layers")
        are_eq = dict_elems_eq(cfg1, cfg2)
        return are_eq

    def plot(self, ax, **kwargs):
        pass

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def configuration(self):
        cfg = dict()
        if hasattr(self, "_kwargs"):
            cfg.update(**self._kwargs)
        for d in self.__dict__:
            if d not in ['uuid', 'ax', 'layers', '_renderer', '_kwargs']:
                cfg.update({d: self.__dict__[d]})

        if self._renderer is not None:
            fig = self._renderer.fig
            is_part_of_gridspec = self.ax in fig.get_axes() and self.ax.get_subplotspec() is not None
            cfg.update({"ax_on_grid": is_part_of_gridspec})
            if is_part_of_gridspec:
                n_rows, n_cols, start, stop = self.ax.get_subplotspec().get_geometry()
                cfg.update({"gridspec": {
                    "n_rows": n_rows,
                    "n_cols": n_cols,
                    "start":  start,
                    "stop":   stop
                }})

        return cfg

    @configuration.setter
    def configuration(self, cfg):
        assert type(cfg) is dict
        if cfg["ax_on_grid"]:
            n_rows, n_cols, start, stop = cfg["gridspec"]
        for key, val in cfg.items():
            self.__setattr__(key, val)
