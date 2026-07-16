import pytest

from movierender.overlays._image import secs_to_string


class TestSecsToString:
    def test_hhmmss_zero(self):
        assert secs_to_string(0) == "00:00:00"

    def test_hhmmss_seconds_only(self):
        assert secs_to_string(45) == "00:00:45"

    def test_hhmmss_minutes_and_seconds(self):
        assert secs_to_string(125) == "00:02:05"

    def test_hhmmss_hours_minutes_seconds(self):
        assert secs_to_string(3661) == "01:01:01"

    def test_hhmmss_large(self):
        assert secs_to_string(7200) == "02:00:00"

    def test_hhmm_format(self):
        assert secs_to_string(3661, string_format="hh:mm") == "01:01"

    def test_hhmm_zero(self):
        assert secs_to_string(0, string_format="hh:mm") == "00:00"

    def test_mmss_format(self):
        assert secs_to_string(125, string_format="mm:ss") == "02:05"

    def test_mmss_with_hours(self):
        # mm:ss falls back to hh:mm:ss when hours > 0
        assert secs_to_string(3661, string_format="mm:ss") == "01:01:01"

    def test_mmss_zero(self):
        assert secs_to_string(0, string_format="mm:ss") == "00:00"

    def test_unknown_format_raises(self):
        with pytest.raises(Exception, match="Timestamp string format not implemented"):
            secs_to_string(100, string_format="ss:mm:hh")

    def test_negative_seconds(self):
        # Negative seconds should still produce a string (floor division behavior)
        result = secs_to_string(-5)
        assert isinstance(result, str)
