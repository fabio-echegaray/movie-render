from fileops.logger import get_logger, silence_loggers
from typer import Typer

from ._render_configfile import render_configuration_file_cmd
from ._render_folder import render_folder_cmd
from ._render_movie import render_movie_cmd

log = get_logger(name='render')
silence_loggers(loggers=["tifffile", "matplotlib", "PIL"], output_log_file="silenced.log")
app = Typer()

app.command(name='folder')(render_folder_cmd)
app.command(name='file')(render_configuration_file_cmd)
app.command(name='movie')(render_movie_cmd)

if __name__ == "__main__":
    app()
