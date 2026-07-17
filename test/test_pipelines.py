from unittest.mock import MagicMock

import numpy as np
import pytest

from movierender.render.pipelines import ImagePipeline, NullImage, PipelineException


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
        mock_renderer = MagicMock()
        mock_renderer.__class__.__name__ = "SequentialMovieRenderer"
        pipeline = ImagePipeline(mock_renderer)
        assert pipeline._renderer is mock_renderer

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
