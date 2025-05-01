from fileops.logger import get_logger, silence_loggers
from typer import Typer

from ._render_folder import render

log = get_logger(name='render')
silence_loggers(loggers=["tifffile", "movierender", "PIL"], output_log_file="silenced.log")
app = Typer()

app.command(name='render')(render)

if __name__ == "__main__":
    app()
