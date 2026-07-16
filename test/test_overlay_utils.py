import numpy as np
import pytest

from movierender.overlays.overlay import iterable_elems_eq, dict_elems_eq, get_kwargs


class TestIterableElemsEq:
    def test_equal_int_lists(self):
        assert iterable_elems_eq([1, 2, 3], [1, 2, 3]) is True

    def test_equal_string_lists(self):
        assert iterable_elems_eq(["a", "b"], ["a", "b"]) is True

    def test_different_length(self):
        assert iterable_elems_eq([1, 2], [1, 2, 3]) is False

    def test_different_type(self):
        assert iterable_elems_eq([1, 2], (1, 2)) is False

    def test_different_values(self):
        assert iterable_elems_eq([1, 2, 3], [1, 2, 4]) is False

    def test_equal_float_lists(self):
        assert iterable_elems_eq([1.0, 2.5], [1.0, 2.5]) is True

    def test_equal_bool_lists(self):
        assert iterable_elems_eq([True, False], [True, False]) is True

    def test_empty_lists(self):
        assert iterable_elems_eq([], []) is True

    def test_dict_in_list(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"a": 1, "b": 2}
        assert iterable_elems_eq([d1], [d2]) is True

    def test_dict_in_list_different(self):
        d1 = {"a": 1}
        d2 = {"a": 2}
        assert iterable_elems_eq([d1], [d2]) is False

    def test_nested_list(self):
        assert iterable_elems_eq([[1, 2], [3, 4]], [[1, 2], [3, 4]]) is True

    def test_nested_list_different(self):
        assert iterable_elems_eq([[1, 2]], [[1, 3]]) is False


class TestDictElemsEq:
    def test_equal_dicts(self):
        assert dict_elems_eq({"a": 1, "b": 2}, {"a": 1, "b": 2}) is True

    def test_different_length(self):
        assert dict_elems_eq({"a": 1}, {"a": 1, "b": 2}) is False

    def test_different_keys(self):
        assert dict_elems_eq({"a": 1}, {"b": 1}) is False

    def test_different_values(self):
        assert dict_elems_eq({"a": 1}, {"a": 2}) is False

    def test_nested_dicts(self):
        d1 = {"a": {"b": 1}}
        d2 = {"a": {"b": 1}}
        assert dict_elems_eq(d1, d2) is True

    def test_nested_dicts_different(self):
        d1 = {"a": {"b": 1}}
        d2 = {"a": {"b": 2}}
        assert dict_elems_eq(d1, d2) is False

    def test_list_value(self):
        d1 = {"a": [1, 2, 3]}
        d2 = {"a": [1, 2, 3]}
        assert dict_elems_eq(d1, d2) is True

    def test_list_value_different(self):
        d1 = {"a": [1, 2]}
        d2 = {"a": [1, 3]}
        assert dict_elems_eq(d1, d2) is False

    def test_none_value(self):
        assert dict_elems_eq({"a": None}, {"a": None}) is True

    def test_empty_dicts(self):
        assert dict_elems_eq({}, {}) is True

    def test_scalar_value(self):
        assert dict_elems_eq({"a": np.float64(3.14)}, {"a": np.float64(3.14)}) is True

    def test_type_mismatch(self):
        assert dict_elems_eq({"a": 1}, [1]) is False


class TestGetKwargs:
    def test_find_in_first_kwargs(self):
        result = get_kwargs([{"x": 10}, {"x": 20}], {"x": 0})
        assert result == [10]

    def test_find_in_second_kwargs(self):
        result = get_kwargs([{}, {"x": 20}], {"x": 0})
        assert result == [20]

    def test_use_default(self):
        result = get_kwargs([{}, {}], {"x": 42})
        assert result == [42]

    def test_multiple_keys(self):
        result = get_kwargs(
            [{"a": 1}, {"b": 2}],
            {"a": 0, "b": 0, "c": 0}
        )
        assert result == [1, 2, 0]

    def test_preserves_order(self):
        result = get_kwargs(
            [{"z": 26, "a": 1}],
            {"a": 0, "z": 0}
        )
        assert result == [1, 26]

    def test_empty_kwargs(self):
        result = get_kwargs([], {"x": 5})
        assert result == [5]

    def test_none_value_stored(self):
        result = get_kwargs([{"x": None}], {"x": 42})
        assert result == [None]
