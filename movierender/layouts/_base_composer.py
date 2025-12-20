import concurrent
import importlib
import os
import uuid
from concurrent import futures
from pathlib import Path

import matplotlib
from fileops.export.config import ConfigMovie
from fileops.logger import get_logger

from movierender.render import MovieRenderer


class BaseLayoutComposer:
    log = get_logger(name='BaseLayoutComposer')

    def __init__(self, movie: ConfigMovie,
                 prefix='', suffix='',
                 overwrite=False,
                 **kwargs):
        self.log.info(f"matplotlib's backend: {matplotlib.get_backend()}")
        self._overwrite = overwrite
        self._movie_configuration_params = movie
        self.renderer: MovieRenderer | None = None
        self._renderer_params = dict(temp_folder=str(uuid.uuid4()))
        self.dpi = 326

        self.fig_title = movie.title
        self.ax_lst = list()

        im = movie.image_file
        fname = movie.movie_filename if len(movie.movie_filename) > 0 else im.image_path.name
        self.filename = prefix + fname
        if len(suffix) > 0:
            self.filename += "." + suffix
        self.filename += ".mp4"
        self.base_folder = movie.configfile.parent
        self.save_file_path = Path(self.base_folder) / self.filename

        if os.path.exists(self.save_file_path):
            if os.path.getsize(self.save_file_path) < 300:  # if size is too small, treat it as if the file didn't exist
                overwrite = True
            if not overwrite:
                self.log.warning(f'File {self.filename} already exists in folder {self.base_folder}.')
                raise FileExistsError

    @property
    def configuration(self):
        cfg = dict()

        cfg["renderer"] = dict()
        cfg["renderer_name"] = self.__class__.__name__
        for d in self.__dict__:
            if d not in ['uuid', 'ax', 'ax_lst', '_movie_configuration_params', 'renderer', '_renderer_params']:
                cfg["renderer"].update({d: self.__dict__[d]})
        cfg["renderer"]["overwrite"] = cfg["renderer"].pop("_overwrite")

        cfg["layers"] = list()
        for ly in self.renderer.layers:
            cfg["layers"].append({"name": ly.__class__.__name__, "config": ly.configuration})
        return cfg

    @configuration.setter
    def configuration(self, cfg):
        assert type(cfg) is dict
        for key, val in cfg.items():
            self.__setattr__(key, val)

    def make_layout(self):
        raise NotImplementedError

    def _render_parallel(self):
        n_cpus = os.cpu_count()
        n_workers = n_cpus
        self.log.info(f"Rendering movie into file {self.save_file_path} using {n_workers} processes.")

        # create a bunch of copies of this composer
        composer_array = [self, ]
        cfg = self.configuration
        lcls = self.__class__
        for i in range(n_workers):
            composer_instance = lcls(self._movie_configuration_params, **cfg["renderer"])
            composer_instance._renderer_params = self._renderer_params
            composer_instance.make_layout()

            # obtain overlay layers that are not coming from make_layout
            c1 = cfg["layers"]
            c2 = composer_instance.configuration["layers"]
            additional_overlays = list()
            for d1 in c1:
                d1_in_c2 = False
                for d2 in c2:
                    if d1["config"] == d2["config"]:  # add d1 only if it's not contained in c2
                        d1_in_c2 = True
                        break
                if d1_in_c2:
                    continue
                additional_overlays.append(d1)

            for o in additional_overlays:
                ovl_module = importlib.import_module(f"movierender.overlays")
                ovrl = getattr(ovl_module, o['name'])
                kwargs = o['config'].pop('_kwargs') if '_kwargs' in o else dict()
                composer_instance.renderer += ovrl(**o['config'], **kwargs)

            composer_array.append(composer_instance)

        # ---------------------------------------------------------------------------------------------------------------
        # here comes the parallel magic!
        # ---------------------------------------------------------------------------------------------------------------
        mov = self._movie_configuration_params

        future_to_mapping = dict()
        with futures.ProcessPoolExecutor(max_workers=n_workers) as executor:
            for k, fr in enumerate(mov.frames):
                renderer = composer_array[k % len(composer_array)].renderer
                future = executor.submit(renderer.render_frame, fr)
                future_to_mapping[future] = k  # Store the index k as the value for the future

            for future in concurrent.futures.as_completed(future_to_mapping):
                k = future_to_mapping[future]
                if (e := future.exception()) is not None:
                    self.log.error(f"exception {e.__class__.__name__}({e}) found at ix {k}")
                self.log.debug(f"finished ix {k}; file {future.result()}.")

        self.renderer.render(filename=str(self.save_file_path), test=False)

    def render(self, parallel=False):
        if parallel:
            self._render_parallel()
        else:
            self.log.info(f"Rendering movie into file {self.save_file_path}.")
            if self.renderer is None:
                raise AttributeError("Need to call method make_layout before trying to render.")
            self.renderer.render(filename=str(self.save_file_path), test=False)
