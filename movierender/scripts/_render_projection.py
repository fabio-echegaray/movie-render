from pathlib import Path

import traceback
import typer
from fileops.image import TifffileOMEImageFile
from tifffile import tifffile
from typing_extensions import Annotated

from fileops.export.config import read_config, ConfigProjection
from fileops.logger import get_logger

log = get_logger(name='render-projection')


def render_projection(prj: ConfigProjection, overwrite=False):
    if len(prj.image_file.zstacks) == 1:
        log.warning("only one z-stack, skipping flat image.")
        return
    elif len(prj.image_file.zstacks) > 1:
        # open read file, write file, and perform z-projection of the read file to then store it
        imf = prj.image_file
        fst_mdi = imf.image(imf.ix_at(0, 0, 0))
        dtype = fst_mdi.image.dtype
        if isinstance(imf, TifffileOMEImageFile):
            tif = imf._tif
            page = tif.series[0].keyframe
            metadata = tif.imagej_metadata
            if metadata is None:
                metadata = {
                    # 'spacing':   3.947368,
                    'unit':      'um',
                    'finterval': imf.time_interval,
                    'fps':       10.0,
                    'axes':      'TCYX',
                    'Labels':    prj.header,
                }
            metadata.update({'axes': 'TCYX'})
            memmap = tifffile.memmap((prj.configfile.parent / (prj.filename + ".tiff")).absolute(),
                                     shape=(len(prj.frames), len(prj.channels), imf.width, imf.height),
                                     dtype='=' + dtype.char,  # force native byte-order
                                     imagej=True,
                                     metadata=metadata,
                                     photometric=page.photometric,
                                     colormap=page.colormap,
                                     resolution=(imf.um_per_pix * 1e6, imf.um_per_pix * 1e6),
                                     # resolutionunit=tifffile.RESUNIT.CENTIMETER,
                                     )
        else:
            memmap = tifffile.memmap(prj.filename + ".tiff",
                                     shape=(len(prj.frames), len(prj.channels), imf.width, imf.height),
                                     dtype='=' + dtype.char,  # force native byte-order
                                     imagej=True,
                                     )

        # iterate through ImageFile and save projected images as TIFF
        for kf, fr in enumerate(prj.frames):
            for kc, ch in enumerate(prj.channels):
                imz = imf.z_projection(fr, ch, projection=prj.zstack_fn, z_subset=prj.zstacks, as_8bit=False)
                memmap[kf, kc, :, :] = imz.image
        memmap.flush()


def render_projection_cmd(
        cfg_path: Annotated[
            Path, typer.Argument(help="Name of the configuration file of the movie to be rendered")],
        with_root_path: Annotated[
            Path, typer.Option(
                help="Path where image files should be looked in if the path in the configuration file is relative. "
                     "If no path is given, the current folder will be used.")] = None,
        show_file_info: Annotated[
            bool, typer.Option(help="To show file metadata information before rendering the movie")] = True,
        overwrite_projection_file: Annotated[
            bool, typer.Option(help="Set true if you want to overwrite the file")] = False,
):
    log.info(f"Reading configuration file {cfg_path}")
    cfg = read_config(cfg_path, with_root_path=with_root_path)

    # cache the info of each media file so projections sharing the same file are not re-queried
    _MISSING = object()
    info_cache: dict = {}

    # make projections specified in configuration file
    for prj in cfg.projections:
        if show_file_info:
            info = info_cache.get(prj.image_file, _MISSING)
            if info is _MISSING:
                info = prj.image_file.info
                info_cache[prj.image_file] = info
            try:
                log.info(f"file {cfg_path}\r\n{info.squeeze(axis=0)}")
            except Exception as e:
                log.error(e)
                log.error(traceback.format_exc())
        render_projection(prj, overwrite=overwrite_projection_file)
