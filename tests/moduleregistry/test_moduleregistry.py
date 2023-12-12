import sys
from collections import namedtuple
from operator import attrgetter

import pytest

from jenkins.plugins import Plugin, PluginVersion
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
    # 'Groovy' plugin in 'inject' property.
    Scenario("s20", v1="453.vcdb_a_c5c99890", op="__ge__", v2="2.0.0"),
    # 'postbuildscript' plugin in 'postbuildscript' publisher.
    Scenario("s21", v1="3.2.0-460.va_fda_0fa_26720", op="__ge__", v2="2.0"),
    # Same, from story: 2009943.
    Scenario("s22", v1="3.1.0-375.v3db_cd92485e1", op="__ge__", v2="2.0"),
    # 'Slack Notification Plugin' in 'slack' publisher, from story: 2009819.
    Scenario("s23", v1="602.v0da_f7458945d", op="__ge__", v2="2.0"),
    # 'preSCMbuildstep' plugin in 'pre_scm_buildstep' wrapper.
    Scenario("s24", v1="44.v6ef4fd97f56e", op="__ge__", v2="0.3"),
    # 'SSH Agent Plugin' plugin in 'ssh_agent_credentials' wrapper.
    Scenario("s25", v1="295.v9ca_a_1c7cc3a_a_", op="__ge__", v2="1.5.0"),
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
    return ModuleRegistry(config, [Plugin(**d) for d in plugin_info])


def test_get_plugin_version_by_short_name(scenario, registry):
    """
    Plugin version should be available by it's short name
    """
    plugin_name = "JankyPlugin1"
    version = registry.get_plugin_version(plugin_name)

    assert isinstance(version, PluginVersion)
    assert version == scenario.v1


def test_get_plugin_version_by_long_name(scenario, registry):
    """
    Plugin version should be available by it's long name
    """
    plugin_name = "Not A Real Plugin"
    version = registry.get_plugin_version(plugin_name)

    assert isinstance(version, PluginVersion)
    assert version == scenario.v1


def test_get_plugin_version_by_alternative_name(scenario, registry):
    version = registry.get_plugin_version("Non-existent name", "Not A Real Plugin")
    assert version == scenario.v1


def test_get_plugin_version_default_value(registry):
    version = registry.get_plugin_version("Non-existent name", default="1.2.3")
    assert isinstance(version, PluginVersion)
    assert version == "1.2.3"


def test_get_plugin_version_for_missing_plugin(registry):
    """
    The goal of this test case is to validate the behavior of
    ModuleRegistry.get_plugin_version when the given plugin cannot be found in
    ModuleRegistry's internal representation of the plugins_info.
    """
    plugin_name = "PluginDoesNotExist"
    version = registry.get_plugin_version(plugin_name)

    assert isinstance(version, PluginVersion)
    assert version == str(sys.maxsize)


def test_get_plugin_version_for_missing_version(registry):
    """
    The goal of this test case is to validate the behavior of
    ModuleRegistry.get_plugin_version when the given plugin shortName returns
    plugin_info dict that has no version string. In a sane world where
    plugin frameworks like Jenkins' are sane this should never happen, but
    I am including this test and the corresponding default behavior
    because, well, it's Jenkins.
    """
    plugin_name = "HerpDerpPlugin"
    version = registry.get_plugin_version(plugin_name)

    assert isinstance(version, PluginVersion)
    assert version == str(sys.maxsize)


def test_plugin_version_comparison(registry, scenario):
    """
    The goal of this test case is to validate that valid tuple versions are
    ordinally correct. That is, for each given scenario, v1.op(v2)==True
    where 'op' is the equality operator defined for the scenario.
    """
    plugin_name = "JankyPlugin1"
    v1 = registry.get_plugin_version(plugin_name)

    op = getattr(v1, scenario.op)
    test = op(scenario.v2)

    assert test, (
        f"Unexpectedly found {v1} {scenario.op} {scenario.v2} == False"
        " when comparing versions!"
    )
