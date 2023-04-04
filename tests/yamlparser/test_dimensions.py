import pytest

from jenkins_jobs.loc_loader import LocDict, LocList
from jenkins_jobs.dimensions import enum_dimensions_params, is_point_included


# Axes, params, exclude, expected resulting params.
cases = [
    (
        ["axis1"],
        {"axis1": 123},
        [],
        [{"axis1": 123}],
    ),
    (
        ["axis1"],
        {"axis1": [123, 456]},
        [],
        [
            {"axis1": 123},
            {"axis1": 456},
        ],
    ),
    (
        ["axis1", "axis2"],
        {"axis1": 123, "axis2": 456},
        [],
        [{"axis1": 123, "axis2": 456}],
    ),
    (
        ["axis1", "axis2"],
        {"axis1": [11, 22], "axis2": 456},
        [],
        [
            {"axis1": 11, "axis2": 456},
            {"axis1": 22, "axis2": 456},
        ],
    ),
    (
        ["axis1", "axis2"],
        {"axis1": [11, 22], "axis2": [33, 44, 55]},
        [],
        [
            {"axis1": 11, "axis2": 33},
            {"axis1": 11, "axis2": 44},
            {"axis1": 11, "axis2": 55},
            {"axis1": 22, "axis2": 33},
            {"axis1": 22, "axis2": 44},
            {"axis1": 22, "axis2": 55},
        ],
    ),
    (
        ["axis1", "axis2", "axis3"],
        {
            "axis1": ["axis1val1", "axis1val2"],
            "axis2": ["axis2val1", "axis2val2"],
            "axis3": ["axis3val1", "axis3val2"],
        },
        [],
        [
            {"axis1": "axis1val1", "axis2": "axis2val1", "axis3": "axis3val1"},
            {"axis1": "axis1val1", "axis2": "axis2val1", "axis3": "axis3val2"},
            {"axis1": "axis1val1", "axis2": "axis2val2", "axis3": "axis3val1"},
            {"axis1": "axis1val1", "axis2": "axis2val2", "axis3": "axis3val2"},
            {"axis1": "axis1val2", "axis2": "axis2val1", "axis3": "axis3val1"},
            {"axis1": "axis1val2", "axis2": "axis2val1", "axis3": "axis3val2"},
            {"axis1": "axis1val2", "axis2": "axis2val2", "axis3": "axis3val1"},
            {"axis1": "axis1val2", "axis2": "axis2val2", "axis3": "axis3val2"},
        ],
    ),
    # Value with parameters.
    (
        ["axis1"],
        {
            "axis1": [
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
            {"axis1": 123, "param_1": "value_1", "param_2": "value_2"},
        ],
    ),
    (
        ["axis1"],
        {
            "axis1": [
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
            {"axis1": "one", "param_1": "value_1_one", "param_2": "value_2_one"},
            {"axis1": "two", "param_1": "value_1_two", "param_2": "value_2_two"},
        ],
    ),
    (
        ["axis1"],
        {
            "axis1": [
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
            {"axis1": "one", "param_1": "value_1_one", "param_2": "value_2_one"},
            {"axis1": "two"},
        ],
    ),
    # Axis value received from another axis parameter.
    (
        ["axis1", "axis2"],
        {
            "axis1": [
                {"one": {"axis2": "axis2_value"}},
            ],
        },
        [],
        [{"axis1": "one", "axis2": "axis2_value"}],
    ),
    # With excludes.
    (
        ["axis1", "axis2", "axis3"],
        {
            "axis1": "axis1val",
            "axis2": ["axis2val1", "axis2val2"],
            "axis3": ["axis3val1", "axis3val2"],
        },
        [
            {  # First exclude.
                "axis2": "axis2val1",
                "axis3": "axis3val2",
            },
            {  # Second exclude.
                "axis3": "axis3val1",
            },
        ],
        [
            # Excluded by second: {"axis1": "axis1val", "axis2": "axis2val1", "axis3": "axis3val1"},
            # Excluded by first: {"axis1": "axis1val", "axis2": "axis2val1", "axis3": "axis3val2"},
            # Excluded by second: {"axis1": "axis1val", "axis2": "axis2val2", "axis3": "axis3val1"},
            {"axis1": "axis1val", "axis2": "axis2val2", "axis3": "axis3val2"},
        ],
    ),
    (
        ["axis1", "axis2", "axis3"],
        {
            "axis1": ["axis1val1", "axis1val2"],
            "axis2": ["axis2val1", "axis2val2"],
            "axis3": ["axis3val1", "axis3val2"],
        },
        [
            {  # First exclude.
                "axis1": "axis1val1",
                "axis2": "axis2val1",
                "axis3": "axis3val2",
            },
            {  # Second exclude.
                "axis2": "axis2val2",
                "axis3": "axis3val1",
            },
        ],
        [
            {"axis1": "axis1val1", "axis2": "axis2val1", "axis3": "axis3val1"},
            # Excluded by first: {"axis1": "axis1val1", "axis2": "axis2val1", "axis3": "axis3val2"},
            # Excluded by second: {"axis1": "axis1val1", "axis2": "axis2val2", "axis3": "axis3val1"},
            {"axis1": "axis1val1", "axis2": "axis2val2", "axis3": "axis3val2"},
            {"axis1": "axis1val2", "axis2": "axis2val1", "axis3": "axis3val1"},
            {"axis1": "axis1val2", "axis2": "axis2val1", "axis3": "axis3val2"},
            # Excluded by second: {"axis1": "axis1val2", "axis2": "axis2val2", "axis3": "axis3val1"},
            {"axis1": "axis1val2", "axis2": "axis2val2", "axis3": "axis3val2"},
        ],
    ),
]


@pytest.mark.parametrize("axes,params,exclude,expected_dimension_params", cases)
def test_dimensions(axes, params, exclude, expected_dimension_params):
    dimension_params = [
        p
        for p in enum_dimensions_params(axes, LocDict(params), defaults={})
        if is_point_included(LocList(exclude), p)
    ]
    assert dimension_params == expected_dimension_params
