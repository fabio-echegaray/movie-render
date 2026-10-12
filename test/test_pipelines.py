from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from matplotlib import pyplot as plt

from movierender.render.pipelines import (
    ImagePipeline, NullImage, PipelineException, CompositeRGBImage, ZProjectionImage,
)


class TestPipelineException:
    def test_is_exception(self):
        assert issubclass(PipelineException, Exception)

    def test_message(self):
        exc = PipelineException("test message")
        assert str(exc) == "test message"


class TestImagePipeline:
    def test_zstack_all(self):
        pipeline = ImagePipeline(zstack="all")
        assert pipeline.zstack == "all"
        assert pipeline.zstack_fn == "max"

    def test_zstack_positive_int(self):
        pipeline = ImagePipeline(zstack=3)
        assert pipeline.zstack == 3
        assert pipeline.zstack_fn is None

    def test_zstack_negative_int(self):
        # Negative zstack falls through to "all" and zstack_fn resolves to None
        # due to the ternary precedence in the constructor
        pipeline = ImagePipeline(zstack=-1)
        assert pipeline.zstack == "all"
        assert pipeline.zstack_fn is None

    def test_zstack_list(self):
        pipeline = ImagePipeline(zstack=[0, 1, 2])
        assert pipeline.zstack == [0, 1, 2]
        assert pipeline.zstack_fn == "max"

    def test_zstack_set(self):
        pipeline = ImagePipeline(zstack={0, 1})
        assert pipeline.zstack == {0, 1}
        assert pipeline.zstack_fn == "max"

    def test_zstack_fn_override(self):
        pipeline = ImagePipeline(zstack=5, zstack_fn="min")
        assert pipeline.zstack == 5
        assert pipeline.zstack_fn == "min"

    def test_zstack_fn_none_explicit(self):
        pipeline = ImagePipeline(zstack=5, zstack_fn=None)
        assert pipeline.zstack_fn is None

    def test_zstack_cmap_default_plasma(self):
        pipeline = ImagePipeline()
        assert pipeline.zstack_cmap == "plasma"

    def test_zstack_cmap_override(self):
        pipeline = ImagePipeline(zstack_cmap="viridis")
        assert pipeline.zstack_cmap == "viridis"

    def test_ax_default_none(self):
        pipeline = ImagePipeline()
        assert pipeline.ax is None

    def test_ax_set(self):
        mock_ax = MagicMock()
        pipeline = ImagePipeline(ax=mock_ax)
        assert pipeline.ax is mock_ax

    def test_renderer_not_set_by_default(self):
        pipeline = ImagePipeline()
        assert pipeline._renderer is None

    def test_renderer_set_from_arg(self):
        from movierender.render import MovieRenderer
        # MagicMock with spec=MovieRenderer passes isinstance checks
        mock_renderer = MagicMock(spec=MovieRenderer)
        pipeline = ImagePipeline(mock_renderer)
        assert pipeline._renderer is mock_renderer

    def test_renderer_set_from_real_renderer(self):
        from movierender.render import MovieRenderer
        from movierender.render.pipelines import ImagePipeline
        # Monkey-patch to skip the complex __init__ for testing
        orig_init = MovieRenderer.__init__
        MovieRenderer.__init__ = lambda self, **kw: None
        try:
            renderer = MovieRenderer()
            renderer.image_pipeline = []
            pipeline = ImagePipeline(renderer)
            assert pipeline._renderer is renderer
        finally:
            MovieRenderer.__init__ = orig_init

    def test_non_renderer_arg_sets_none(self):
        pipeline = ImagePipeline("not a renderer")
        assert pipeline._renderer is None

    def test_call_raises_not_implemented(self):
        pipeline = ImagePipeline()
        with pytest.raises(NotImplementedError):
            pipeline()


class TestNullImage:
    def test_returns_zeros(self):
        null = NullImage()
        result = null()
        assert result.shape == (1, 1)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, np.zeros((1, 1), dtype=np.uint8))

    def test_inherits_image_pipeline(self):
        assert issubclass(NullImage, ImagePipeline)


class _StubImage:
    """Bare stub that satisfies what ZProjectionImage.__call__ needs."""
    height = width = 8

    def z_projection(self, frame=0, channel=0, z_subset=None, projection='max',
                     as_8bit=False):
        img = np.zeros((8, 8), dtype=np.uint16)
        img[0, 0] = 1000
        return SimpleNamespace(image=img)


class TestCompositeRGBImage:
    def test_inherits_pipeline(self):
        assert issubclass(CompositeRGBImage, ImagePipeline)

    def test_depth_zstack_fn_raises(self):
        with pytest.raises(PipelineException, match="Depth-coded"):
            CompositeRGBImage(
                channeldict={0: {'id': 0, 'color': 'green', 'intensity': 1.0}},
                zstack=[0, 1, 2],
                zstack_fn='all-depth',
            )

    def test_depth_zstack_string_raises(self):
        with pytest.raises(PipelineException, match="Depth-coded"):
            CompositeRGBImage(
                channeldict={0: {'id': 0, 'color': 'green', 'intensity': 1.0}},
                zstack='all-depth',
            )

    def test_non_depth_projection_initialises(self):
        comp = CompositeRGBImage(
            channeldict={0: {'id': 0, 'color': 'green', 'intensity': 1.0}},
            zstack=[0, 1, 2],
            zstack_fn='all-max',
        )
        assert comp.zstack_fn == 'all-max'

    def test_merge_tints_and_sums(self):
        # each channel is gray2rgb'ed, tinted by its colour and scaled by its
        # intensity, then summed onto the background
        class NestedImage:
            height = width = 4

            def z_projection(self, *args, **kwargs):
                return SimpleNamespace(image=np.full((4, 4), 0.5, dtype=np.float64))

        comp = CompositeRGBImage(
            channeldict={
                0: {'id': 0, 'color': 'red', 'intensity': 1.0},
                1: {'id': 1, 'color': 'blue', 'intensity': 0.5},
            },
            zstack=[0, 1, 2],
            zstack_fn='all-max',
        )
        comp._renderer = SimpleNamespace(image=NestedImage(), frame=0)
        out = comp()
        assert out.shape == (4, 4, 3)
        np.testing.assert_allclose(out[0, 0], (0.5, 0.0, 0.25), atol=1e-9)


class TestZProjectionImage:
    def test_inherits_pipeline(self):
        assert issubclass(ZProjectionImage, ImagePipeline)

    def test_default_projection(self):
        pipe = ZProjectionImage(zstack=[0, 1, 2])
        assert pipe.zstack_fn == 'max'

    def test_projection_rendered(self):
        pipe = ZProjectionImage(zstack=[0, 1, 2, 3], zstack_fn='all-max')
        pipe._renderer = SimpleNamespace(image=_StubImage(), frame=0)
        img = pipe(frame=0)
        assert img.shape == (8, 8)
        assert img.dtype != np.float64  # not normalised away

    def test_depth_is_colourised(self):
        # ground-truth data: bottom-left pixel peaks at the bottom of the
        # stack, top-right at the top; brightness follows the max projection
        vol = np.zeros((4, 8, 8))
        vol[0, 0, 0] = 1.0
        vol[3, 7, 7] = 2.0

        with patch("movierender.colorize.z_volume", return_value=vol):
            pipe = ZProjectionImage(zstack=[0, 1, 2, 3], zstack_fn='all-depth', zstack_cmap='plasma')
            pipe._renderer = SimpleNamespace(image=object(), frame=0)
            img = pipe(frame=0)
        assert img.shape == (8, 8, 3)
        plasma = plt.get_cmap('plasma')
        np.testing.assert_allclose(img[7, 7], plasma(1.0)[:3], atol=1e-9)
        np.testing.assert_allclose(img[0, 0], np.asarray(plasma(0.0)[:3]) * 0.5, atol=1e-9)
        np.testing.assert_allclose(img[3, 3], 0.0, atol=1e-12)

    def test_constructor_channel_used_when_called_without_args(self):
        # the renderer invokes pipelines with no arguments (``imgp()``), so the
        # constructor's ``channel`` must be honoured, not call-time default 0
        seen = {}

        class NestedImage:
            height = width = 4

            def z_projection(self, *args, **kwargs):
                seen['channel'] = kwargs['channel']
                seen['z_subset'] = kwargs['z_subset']
                return SimpleNamespace(image=np.zeros((4, 4), dtype=np.uint16))

        pipe = ZProjectionImage(channel=2, zstack=[0, 1], zstack_fn='all-max')
        pipe._renderer = SimpleNamespace(image=NestedImage(), frame=3)
        pipe()
        assert seen['channel'] == 2
        assert seen['z_subset'] == [0, 1]

    def test_constructor_channel_used_for_depth(self):
        with patch("movierender.colorize.z_volume", return_value=np.zeros((1, 4, 4))) as zvol:
            pipe = ZProjectionImage(channel=2, zstack=[0], zstack_fn='all-depth')
            pipe._renderer = SimpleNamespace(image=object(), frame=3)
            pipe()
        assert zvol.call_args.kwargs['channel'] == 2

    def test_explicit_call_channel_overrides_constructor(self):
        with patch("movierender.colorize.z_volume", return_value=np.zeros((1, 4, 4))) as zvol:
            pipe = ZProjectionImage(channel=2, zstack=[0], zstack_fn='all-depth')
            pipe._renderer = SimpleNamespace(image=object(), frame=3)
            pipe(channel=1)
        assert zvol.call_args.kwargs['channel'] == 1

    def test_zstack_string_means_whole_stack(self):
        # a bare 'all' must NOT reach FileOps as z_subset (a str would be
        # iterated character by character)
        seen = {}

        class NestedImage:
            height = width = 4

            def z_projection(self, *args, **kwargs):
                seen['z_subset'] = kwargs['z_subset']
                return SimpleNamespace(image=np.zeros((4, 4), dtype=np.uint16))

        pipe = ZProjectionImage(zstack='all', zstack_fn='max')
        pipe._renderer = SimpleNamespace(image=NestedImage(), frame=0)
        pipe()
        assert seen['z_subset'] is None

    def test_depth_zstack_string_uses_whole_stack(self):
        with patch("movierender.colorize.z_volume", return_value=np.zeros((1, 4, 4))) as zvol:
            pipe = ZProjectionImage(zstack='all', zstack_fn='all-depth')
            pipe._renderer = SimpleNamespace(image=object(), frame=0)
            pipe()
        assert zvol.call_args.kwargs['z_subset'] is None

    def test_single_plane_raises(self):
        pipe = ZProjectionImage(zstack=2, zstack_fn='max')
        pipe._renderer = SimpleNamespace(image=_StubImage(), frame=0)
        with pytest.raises(ValueError, match="single z-plane"):
            pipe(frame=0)

    def test_no_source_raises(self):
        pipe = ZProjectionImage(zstack=[0])
        with pytest.raises(ValueError, match="No image source"):
            pipe(frame=0)
