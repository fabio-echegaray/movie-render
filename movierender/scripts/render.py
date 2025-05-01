from fileops.logger import get_logger, silence_loggers
from typer import Typer

from ._render_folder import render
from ._render_movie import render_configuration_file

log = get_logger(name='render')
silence_loggers(loggers=["tifffile", "movierender", "PIL"], output_log_file="silenced.log")
app = Typer()

app.command(name='folder')(render)
app.command(name='file')(render_configuration_file)

if __name__ == "__main__":
    app()
