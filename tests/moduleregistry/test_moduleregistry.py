import pkg_resources
from collections import namedtuple
from operator import attrgetter

import pytest

from jenkins_jobs.config import JJBConfig
from jenkins_jobs.registry import ModuleRegistry


Scenario = namedtuple("Scnenario", "name v1 op v2")


scenarios = [
    Scenario("s1", v1="1.0.0", op="__gt__", v2="0.8.0"),
    Scenario("s2", v1="1.0.1alpha", op="__gt__", v2="1.0.0"),
    Scenario("s3", v1="1.0", op="__eq__", v2="1.0.0"),
    Scenario("s4", v1="1.0", op="__eq__", v2="1.0"),
    Scenario("s5", v1="1.0", op="__lt__", v2="1.8.0"),
    Scenario("s6", v1="1.0.1alpha", op="__lt__", v2="1.0.1"),
    Scenario("s7", v1="1.0alpha", op="__lt__", v2="1.0.0"),
    Scenario("s8", v1="1.0-alpha", op="__lt__", v2="1.0.0"),
    Scenario("s9", v1="1.1-alpha", op="__gt__", v2="1.0"),
    Scenario("s10", v1="1.0-SNAPSHOT", op="__lt__", v2="1.0"),
    Scenario("s11", v1="1.0.preview", op="__lt__", v2="1.0"),
    Scenario("s12", v1="1.1-SNAPSHOT", op="__gt__", v2="1.0"),
    Scenario("s13", v1="1.0a-SNAPSHOT", op="__lt__", v2="1.0a"),
    Scenario(
        "s14", v1="1.4.6-SNAPSHOT (private-0986edd9-example)", op="__lt__", v2="1.4.6"
    ),
    Scenario(
        "s15", v1="1.4.6-SNAPSHOT (private-0986edd9-example)", op="__gt__", v2="1.4.5"
    ),
    Scenario("s16", v1="1.0.1-1.v1", op="__gt__", v2="1.0.1"),
    Scenario("s17", v1="1.0.1-1.v1", op="__lt__", v2="1.0.2"),
    Scenario("s18", v1="1.0.2-1.v1", op="__gt__", v2="1.0.1"),
    Scenario("s19", v1="1.0.2-1.v1", op="__gt__", v2="1.0.1-2"),
]


@pytest.fixture(
    params=scenarios,
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


@pytest.fixture
def config():
    config = JJBConfig()
    config.validate()
    return config


@pytest.fixture
def registry(config, scenario):
    plugin_info = [
        {
            "shortName": "HerpDerpPlugin",
            "longName": "Blah Blah Blah Plugin",
        },
        {
            "shortName": "JankyPlugin1",
            "longName": "Not A Real Plugin",
            "version": scenario.v1,
        },
    ]
    return ModuleRegistry(config, plugin_info)


def test_get_plugin_info_dict(registry):
    """
    The goal of this test is to validate that the plugin_info returned by
    ModuleRegistry.get_plugin_info is a dictionary whose key 'shortName' is
    the same value as the string argument passed to
    ModuleRegistry.get_plugin_info.
    """
    plugin_name = "JankyPlugin1"
    plugin_info = registry.get_plugin_info(plugin_name)

    assert isinstance(plugin_info, dict)
    assert plugin_info["shortName"] == plugin_name


def test_get_plugin_info_dict_using_longName(registry):
    """
    The goal of this test is to validate that the plugin_info returned by
    ModuleRegistry.get_plugin_info is a dictionary whose key 'longName' is
    the same value as the string argument passed to
    ModuleRegistry.get_plugin_info.
    """
    plugin_name = "Blah Blah Blah Plugin"
    plugin_info = registry.get_plugin_info(plugin_name)

    assert isinstance(plugin_info, dict)
    assert plugin_info["longName"] == plugin_name


def test_get_plugin_info_dict_no_plugin(registry):
    """
    The goal of this test case is to validate the behavior of
    ModuleRegistry.get_plugin_info when the given plugin cannot be found in
    ModuleRegistry's internal representation of the plugins_info.
    """
    plugin_name = "PluginDoesNotExist"
    plugin_info = registry.get_plugin_info(plugin_name)

    assert isinstance(plugin_info, dict)
    assert plugin_info == {}


def test_get_plugin_info_dict_no_version(registry):
    """
    The goal of this test case is to validate the behavior of
    ModuleRegistry.get_plugin_info when the given plugin shortName returns
    plugin_info dict that has no version string. In a sane world where
    plugin frameworks like Jenkins' are sane this should never happen, but
    I am including this test and the corresponding default behavior
    because, well, it's Jenkins.
    """
    plugin_name = "HerpDerpPlugin"
    plugin_info = registry.get_plugin_info(plugin_name)

    assert isinstance(plugin_info, dict)
    assert plugin_info["shortName"] == plugin_name
    assert plugin_info["version"] == "0"


def test_plugin_version_comparison(registry, scenario):
    """
    The goal of this test case is to validate that valid tuple versions are
    ordinally correct. That is, for each given scenario, v1.op(v2)==True
    where 'op' is the equality operator defined for the scenario.
    """
    plugin_name = "JankyPlugin1"
    plugin_info = registry.get_plugin_info(plugin_name)
    v1 = plugin_info.get("version")

    op = getattr(pkg_resources.parse_version(v1), scenario.op)
    test = op(pkg_resources.parse_version(scenario.v2))

    assert test, (
        f"Unexpectedly found {v1} {scenario.v2} {scenario.op} == False"
        " when comparing versions!"
    )
