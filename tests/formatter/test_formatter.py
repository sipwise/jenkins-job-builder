import pytest
from jinja2 import StrictUndefined

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.formatter import (
    CustomFormatter,
    enum_str_format_required_params,
    enum_str_format_param_defaults,
)


class AnObject:
    def __init__(self, val):
        self.val = val


# Format, kwargs, used kwargs, defaults, result.
cases = [
    # Single variable, whole string.
    ("{abc}", {"abc": "123"}, {"abc"}, {}, "123"),
    ("{abc:>5}", {"abc": "123"}, {"abc"}, {}, "  123"),
    ("{abc:d}", {"abc": 123}, {"abc"}, {}, "123"),
    ("{abc|555}", {"abc": "123"}, {"abc"}, {"abc": "555"}, "123"),
    ("{abc|555}", {}, {"abc"}, {"abc": "555"}, "555"),
    pytest.param(
        "{abc|555:d}",
        {},
        {"abc"},
        {"abc": "555"},
        "555",
        marks=pytest.mark.xfail(reason="Format specifier for default is not supported"),
    ),
    # Retain original object type when whole string is a variable template.
    ("{obj:abc}", {"abc": "123"}, {"abc"}, {}, "123"),
    ("{obj:abc}", {"abc": 123}, {"abc"}, {}, 123),
    ("{abc}", {"abc": 123}, {"abc"}, {}, 123),
    ("{obj:abc|555}", {"abc": 123}, {"abc"}, {"abc": "555"}, 123),
    ("{abc|555}", {"abc": 123}, {"abc"}, {"abc": "555"}, 123),
    ("{obj:abc}", {"abc": [1, 2, 3]}, {"abc"}, {}, [1, 2, 3]),
    ("{abc}", {"abc": [1, 2, 3]}, {"abc"}, {}, [1, 2, 3]),
    ("{obj:abc|555}", {}, {"abc"}, {"abc": "555"}, "555"),
    # Single variable.
    (" {abc} ", {"abc": "123"}, {"abc"}, {}, " 123 "),
    (" {abc:<5} ", {"abc": "123"}, {"abc"}, {}, " 123   "),
    (" {abc|555} ", {"abc": "123"}, {"abc"}, {"abc": "555"}, " 123 "),
    (" {abc|555} ", {}, {"abc"}, {"abc": "555"}, " 555 "),
    ("x{abc}y", {"abc": "123"}, {"abc"}, {}, "x123y"),
    ("x {abc} y", {"abc": "123"}, {"abc"}, {}, "x 123 y"),
    ("x {abc|555} y", {"abc": "123"}, {"abc"}, {"abc": "555"}, "x 123 y"),
    # Quoted single variable, while string.
    ("{{abc}}", {"abc": "123"}, {}, {}, "{abc}"),
    ("{{abc|555}}", {"abc": "123"}, {}, {}, "{abc|555}"),
    ("{{obj:abc}}", {"abc": "123"}, {}, {}, "{obj:abc}"),
    ("{{obj:abc|555}}", {"abc": "123"}, {}, {}, "{obj:abc|555}"),
    # Quoted single variable.
    (" {{abc}} ", {"abc": "123"}, {}, {}, " {abc} "),
    ("x{{abc}}y", {"abc": "123"}, {}, {}, "x{abc}y"),
    ("x {{abc}} y", {"abc": "123"}, {}, {}, "x {abc} y"),
    # Multiple variables.
    ("{a}{b}", {"a": "12", "b": "34"}, {"a", "b"}, {}, "1234"),
    (" {a} {b} ", {"a": "12", "b": "34"}, {"a", "b"}, {}, " 12 34 "),
    (" {a|555} {b} ", {"a": "12", "b": "34"}, {"a", "b"}, {"a": "555"}, " 12 34 "),
    (" {a|555} {b} ", {"b": "34"}, {"a", "b"}, {"a": "555"}, " 555 34 "),
    ("x{a}y{b}z", {"a": "12", "b": "34"}, {"a", "b"}, {}, "x12y34z"),
    ("x {a} y {b} z", {"a": "12", "b": "34"}, {"a", "b"}, {}, "x 12 y 34 z"),
    ("x {a:<4} y {b} z", {"a": "12", "b": "34"}, {"a", "b"}, {}, "x 12   y 34 z"),
    # Quoted multiple variables
    ("{{a}}{{b}}", {"a": "12", "b": "34"}, {}, {}, "{a}{b}"),
    (" {{a}} {{b}} ", {"a": "12", "b": "34"}, {}, {}, " {a} {b} "),
    ("x{{a}}y{{b}}z", {"a": "12", "b": "34"}, {}, {}, "x{a}y{b}z"),
    ("x {{a}} y {{b}} z", {"a": "12", "b": "34"}, {}, {}, "x {a} y {b} z"),
    ("x {{a}} y {{b|555}} z", {"a": "12", "b": "34"}, {}, {}, "x {a} y {b|555} z"),
    # Multiple-quoted.
    pytest.param(
        "{{{abc}}}",
        {"abc": "123"},
        {},
        {},
        "{123}",
        marks=pytest.mark.xfail(reason="Bug"),
    ),  # Actual result: "123".
    (" {{{abc}}} ", {"abc": "123"}, {"abc"}, {}, " {123} "),
    ("x{{{abc}}}y", {"abc": "123"}, {"abc"}, {}, "x{123}y"),
    ("{{{{abc}}}}", {"abc": "123"}, {}, {}, "{{abc}}"),
    (" {{{{abc}}}} ", {"abc": "123"}, {}, {}, " {{abc}} "),
    ("x{{{{abc}}}}y", {"abc": "123"}, {}, {}, "x{{abc}}y"),
    ("x{{{{abc:30}}}}y", {"abc": "123"}, {}, {}, "x{{abc:30}}y"),
    # With attribute/item getters.
    ("{abc.val}", {"abc": AnObject("123")}, {"abc"}, {}, "123"),
    ("x{abc.val}y", {"abc": AnObject("123")}, {"abc"}, {}, "x123y"),
    pytest.param(
        "{abc.val|xy}",
        {},
        {"abc"},
        {"abc": "xy"},
        "xy",
        marks=pytest.mark.xfail(reason="Default for complex values is not supported"),
    ),
    ("{abc[1]}", {"abc": ["12", "34", "56"]}, {"abc"}, {}, "34"),
    ("x{abc[1]}y", {"abc": ["12", "34", "56"]}, {"abc"}, {}, "x34y"),
    pytest.param(
        "{abc[1]|xy}",
        {},
        {"abc"},
        {"abc": "xy"},
        "xy",
        marks=pytest.mark.xfail(reason="Default for complex values is not supported"),
    ),
    # Quoted with attribute/item getters.
    ("{{abc.val}}", {"abc": AnObject("123")}, {}, {}, "{abc.val}"),
    ("x{{abc.val}}y", {"abc": AnObject("123")}, {}, {}, "x{abc.val}y"),
    ("{{abc.val|xy}}", {}, {}, {}, "{abc.val|xy}"),
    ("{{abc[1]}}", {"abc": ["12", "34", "56"]}, {}, {}, "{abc[1]}"),
    ("x{{abc[1]}}y", {"abc": ["12", "34", "56"]}, {}, {}, "x{abc[1]}y"),
    ("{{abc[1]|xy}}", {}, {}, {}, "{abc[1]|xy}"),
    # With formatters.
    ("{abc!r}", {"abc": "123"}, {"abc"}, {}, "'123'"),
    ("x{abc!r}y", {"abc": "123"}, {"abc"}, {}, "x'123'y"),
    # Quoted with formatters.
    ("{{abc!r}}", {"abc": "123"}, {}, {}, "{abc!r}"),
    ("x{{abc!r}}y", {"abc": "123"}, {}, {}, "x{abc!r}y"),
    # Multiple defaults
    (
        " {a|555} {b|666} {c|} ",
        {},
        {"a", "b", "c"},
        {"a": "555", "b": "666", "c": ""},
        " 555 666  ",
    ),
]


@pytest.mark.parametrize(
    "format,vars,used_vars,expected_defaults,expected_result", cases
)
def test_format(format, vars, used_vars, expected_defaults, expected_result):
    formatter = CustomFormatter(allow_empty=False)
    result = formatter.format(format, **vars)
    assert result == expected_result


@pytest.mark.parametrize(
    "format,vars,expected_used_vars,expected_defaults,expected_result", cases
)
def test_used_params(
    format, vars, expected_used_vars, expected_defaults, expected_result
):
    used_vars = set(enum_str_format_required_params(format, pos=None))
    assert used_vars == set(expected_used_vars)


@pytest.mark.parametrize(
    "format,vars,expected_used_vars,expected_defaults,expected_result", cases
)
def test_defaults(format, vars, expected_used_vars, expected_defaults, expected_result):
    defaults = dict(enum_str_format_param_defaults(format))
    assert defaults == expected_defaults


positional_cases = [
    "{}",
    "{:d}",
    "{!r}",
    "{[1]}",
    "{[1]:d}",
    "{[1]!r}",
    "{.abc}",
    "{.abc:d}",
    "{.abc!r}",
    "{0}",
    "{2}",
    "{2:<5}",
    "{2!r}",
    "{2.abc}",
    "{2.abc!r}",
    "{1[2]}",
    "{1[2]!r}",
    " {} ",
    " {1} ",
    "x{}y",
    "x{2}y",
    "x {} y",
    "x {0} y",
    "{abc}{}",
    " {abc} {1} ",
    " {abc} {1!r} ",
    "x{abc}y{}z",
    "x{abc} y {1} z",
    "x{abc} y {1.abc} z",
    "x{abc} y {1.abc:d} z",
]


@pytest.mark.parametrize("format", positional_cases)
def test_positional_args(format):
    formatter = CustomFormatter(allow_empty=False)
    with pytest.raises(JenkinsJobsException) as excinfo:
        list(formatter.enum_required_params(format))
    message = f"Positional format arguments are not supported: {format!r}"
    assert str(excinfo.value) == message


def test_undefined_with_default_whole():
    formatter = CustomFormatter(allow_empty=False)
    format = "{missing|default_value}"
    params = {"missing": StrictUndefined(name="missing")}
    result = formatter.format(format, **params)
    assert result == "default_value"


def test_undefined_with_default():
    formatter = CustomFormatter(allow_empty=False)
    format = "[{missing|default_value}]"
    params = {"missing": StrictUndefined(name="missing")}
    result = formatter.format(format, **params)
    assert result == "[default_value]"
