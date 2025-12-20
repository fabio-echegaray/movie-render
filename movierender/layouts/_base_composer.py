import os
from pathlib import Path

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger

from movierender.render import MovieRenderer


class BaseLayoutComposer:
    log = get_logger(name='BaseLayoutComposer')

    def __init__(self, movie: ConfigMovie,
                 prefix='', suffix='',
                 overwrite=False,
                 **kwargs):
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

    def render(self):
        self.log.info(f"Rendering movie into file {self.save_file_path}.")
        if self.renderer is None:
            raise AttributeError("Need to call method make_layout before trying to render.")
        self.renderer.render(filename=str(self.save_file_path), test=False)
