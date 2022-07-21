import pytest

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.dimensions import DimensionsExpander


# Axes, params, exclude, expected resulting params.
cases = [
    (
        ["axe1"],
        {"axe1": 123},
        [],
        [{"axe1": 123}],
    ),
    (
        ["axe1"],
        {"axe1": [123, 456]},
        [],
        [
            {"axe1": 123},
            {"axe1": 456},
        ],
    ),
    (
        ["axe1", "axe2"],
        {"axe1": 123, "axe2": 456},
        [],
        [{"axe1": 123, "axe2": 456}],
    ),
    (
        ["axe1", "axe2"],
        {"axe1": [11, 22], "axe2": 456},
        [],
        [
            {"axe1": 11, "axe2": 456},
            {"axe1": 22, "axe2": 456},
        ],
    ),
    (
        ["axe1", "axe2"],
        {"axe1": [11, 22], "axe2": [33, 44, 55]},
        [],
        [
            {"axe1": 11, "axe2": 33},
            {"axe1": 11, "axe2": 44},
            {"axe1": 11, "axe2": 55},
            {"axe1": 22, "axe2": 33},
            {"axe1": 22, "axe2": 44},
            {"axe1": 22, "axe2": 55},
        ],
    ),
    (
        ["axe1", "axe2", "axe3"],
        {
            "axe1": ["axe1val1", "axe1val2"],
            "axe2": ["axe2val1", "axe2val2"],
            "axe3": ["axe3val1", "axe3val2"],
        },
        [],
        [
            {"axe1": "axe1val1", "axe2": "axe2val1", "axe3": "axe3val1"},
            {"axe1": "axe1val1", "axe2": "axe2val1", "axe3": "axe3val2"},
            {"axe1": "axe1val1", "axe2": "axe2val2", "axe3": "axe3val1"},
            {"axe1": "axe1val1", "axe2": "axe2val2", "axe3": "axe3val2"},
            {"axe1": "axe1val2", "axe2": "axe2val1", "axe3": "axe3val1"},
            {"axe1": "axe1val2", "axe2": "axe2val1", "axe3": "axe3val2"},
            {"axe1": "axe1val2", "axe2": "axe2val2", "axe3": "axe3val1"},
            {"axe1": "axe1val2", "axe2": "axe2val2", "axe3": "axe3val2"},
        ],
    ),
    # Value with parameters.
    (
        ["axe1"],
        {
            "axe1": [
                {
                    123: {
                        "param_1": "value_1",
                        "param_2": "value_2",
                    }
                },
            ]
        },
        [],
        [
            {"axe1": 123, "param_1": "value_1", "param_2": "value_2"},
        ],
    ),
    (
        ["axe1"],
        {
            "axe1": [
                {
                    "one": {
                        "param_1": "value_1_one",
                        "param_2": "value_2_one",
                    }
                },
                {
                    "two": {
                        "param_1": "value_1_two",
                        "param_2": "value_2_two",
                    }
                },
            ]
        },
        [],
        [
            {"axe1": "one", "param_1": "value_1_one", "param_2": "value_2_one"},
            {"axe1": "two", "param_1": "value_1_two", "param_2": "value_2_two"},
        ],
    ),
    (
        ["axe1"],
        {
            "axe1": [
                {
                    "one": {
                        "param_1": "value_1_one",
                        "param_2": "value_2_one",
                    }
                },
                "two",
            ]
        },
        [],
        [
            {"axe1": "one", "param_1": "value_1_one", "param_2": "value_2_one"},
            {"axe1": "two"},
        ],
    ),
    # With excludes.
    (
        ["axe1", "axe2", "axe3"],
        {
            "axe1": "axe1val",
            "axe2": ["axe2val1", "axe2val2"],
            "axe3": ["axe3val1", "axe3val2"],
        },
        [
            {  # First exclude.
                "axe2": "axe2val1",
                "axe3": "axe3val2",
            },
            {  # Second exclude.
                "axe3": "axe3val1",
            },
        ],
        [
            # Excluded by second: {"axe1": "axe1val", "axe2": "axe2val1", "axe3": "axe3val1"},
            # Excluded by first: {"axe1": "axe1val", "axe2": "axe2val1", "axe3": "axe3val2"},
            # Excluded by second: {"axe1": "axe1val", "axe2": "axe2val2", "axe3": "axe3val1"},
            {"axe1": "axe1val", "axe2": "axe2val2", "axe3": "axe3val2"},
        ],
    ),
    (
        ["axe1", "axe2", "axe3"],
        {
            "axe1": ["axe1val1", "axe1val2"],
            "axe2": ["axe2val1", "axe2val2"],
            "axe3": ["axe3val1", "axe3val2"],
        },
        [
            {  # First exclude.
                "axe1": "axe1val1",
                "axe2": "axe2val1",
                "axe3": "axe3val2",
            },
            {  # Second exclude.
                "axe2": "axe2val2",
                "axe3": "axe3val1",
            },
        ],
        [
            {"axe1": "axe1val1", "axe2": "axe2val1", "axe3": "axe3val1"},
            # Excluded by first: {"axe1": "axe1val1", "axe2": "axe2val1", "axe3": "axe3val2"},
            # Excluded by second: {"axe1": "axe1val1", "axe2": "axe2val2", "axe3": "axe3val1"},
            {"axe1": "axe1val1", "axe2": "axe2val2", "axe3": "axe3val2"},
            {"axe1": "axe1val2", "axe2": "axe2val1", "axe3": "axe3val1"},
            {"axe1": "axe1val2", "axe2": "axe2val1", "axe3": "axe3val2"},
            # Excluded by second: {"axe1": "axe1val2", "axe2": "axe2val2", "axe3": "axe3val1"},
            {"axe1": "axe1val2", "axe2": "axe2val2", "axe3": "axe3val2"},
        ],
    ),
]


@pytest.mark.parametrize("axes,params,exclude,expected_dimension_params", cases)
def test_dimensions(axes, params, exclude, expected_dimension_params):
    dim_expander = DimensionsExpander(context=None)
    dimension_params = [
        p
        for p in dim_expander.enum_dimensions_params(axes, params, defaults={})
        if dim_expander.is_point_included(exclude, p)
    ]
    assert dimension_params == expected_dimension_params


def test_missing_param():
    dim_expander = DimensionsExpander(context="test-job")
    with pytest.raises(JenkinsJobsException) as excinfo:
        list(
            dim_expander.enum_dimensions_params(
                axes=["missing-axis"],
                params={},
                defaults={},
            )
        )
    message = "Template 'test-job' contains parameter 'missing-axis', but it was never defined"
    assert str(excinfo.value) == message
