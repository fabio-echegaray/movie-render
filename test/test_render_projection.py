from types import SimpleNamespace

from movierender.scripts._render_projection import projection_memmap_plan


def _prj(zstack_fn, frames=(0, 1), channels=(0,)):
    return SimpleNamespace(frames=frames, channels=channels, zstack_fn=zstack_fn)


def _imf(width=64, height=32):
    return SimpleNamespace(width=width, height=height)


def test_depth_projection_gets_rgb_axis():
    shape, dtype = projection_memmap_plan(_prj("all-depth"), _imf(), source_dtype_char="H")
    assert shape == (2, 1, 64, 32, 3)
    assert dtype == "=f4"


def test_plain_projection_keeps_source_dtype():
    shape, dtype = projection_memmap_plan(_prj("all-max"), _imf(), source_dtype_char="H")
    assert shape == (2, 1, 64, 32)
    assert dtype == "=H"


def test_plain_float_projection_keeps_float_dtype():
    _, dtype = projection_memmap_plan(_prj("max"), _imf(), source_dtype_char="d")
    assert dtype == "=d"


def test_depth_via_code_alias():
    shape, _ = projection_memmap_plan(_prj("all-code"), _imf(), source_dtype_char="H")
    assert shape[-1] == 3