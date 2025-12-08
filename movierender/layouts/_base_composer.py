import os

from fileops.export.config import ConfigMovie
from fileops.logger import get_logger


class BaseLayoutComposer:
    log = get_logger(name='BaseLayoutComposer')

    def __init__(self, movie: ConfigMovie,
                 prefix='', suffix='',
                 overwrite=False,
                 **kwargs):
        self._overwrite = overwrite
        self._movie_configuration_params = movie
        self.renderer = None
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
        self.save_file_path = os.path.join(self.base_folder, self.filename)
        if os.path.exists(self.save_file_path):
            if os.path.getsize(self.save_file_path) < 300:  # if size is too small, treat it as if the file didn't exist
                overwrite = True
            if not overwrite:
                self.log.warning(f'File {self.filename} already exists in folder {self.base_folder}.')
                raise FileExistsError

    def make_layout(self):
        raise NotImplementedError

    def render(self):
        self.log.info(f"Rendering movie into file {self.save_file_path}.")
        self.renderer.render(filename=self.save_file_path, test=False)
