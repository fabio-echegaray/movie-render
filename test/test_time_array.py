import pytest

from movierender.layouts.panel._time_array import assert_supported_merge_projection


class TestMergeDepthGuard:
    @pytest.mark.parametrize("zstack_fn", ["depth", "all-depth", "code", "all-code"])
    def test_depth_merge_raises(self, zstack_fn):
        with pytest.raises(ValueError, match="Depth-coded"):
            assert_supported_merge_projection(zstack_fn)

    @pytest.mark.parametrize("zstack_fn", [None, "max", "all-max", "mean", "all-mean"])
    def test_plain_merge_is_allowed(self, zstack_fn):
        assert_supported_merge_projection(zstack_fn)