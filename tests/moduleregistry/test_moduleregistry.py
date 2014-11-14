import testtools as tt
from testtools.content import text_content
from testscenarios.testcase import TestWithScenarios
from six.moves import configparser, StringIO

from jenkins_jobs import cmd
from jenkins_jobs.builder import ModuleRegistry


def generate_plugin_info_list(plugin_name, **kwargs):
    return [dict(longName=plugin_name, **kwargs),
            ]


class ModuleRegistryPluginInfoTestsWithScenarios(TestWithScenarios,
                                                 tt.TestCase):
    scenarios = [
        ('s1', dict(v1='1.0.0', op='__lt__', v2='1.0.1')),
        ('s2', dict(v1='1.0.1', op='__eq__', v2='1.0.1')),
        ('s3', dict(v1='1.0.1alpha', op='__gt__', v2='1.0.1')),
        ('s2', dict(v1='1', op='__lt__', v2='1.1')),
        ('s2', dict(v1='derp', op='__gt__', v2='1.1')),
        ('s2', dict(v1='1', op='__gt__', v2='0')),
    ]

    def setUp(self):
        super(ModuleRegistryPluginInfoTestsWithScenarios, self).setUp()

        config = configparser.ConfigParser()
        config.readfp(StringIO(cmd.DEFAULT_CONF))

        plugin_info = generate_plugin_info_list("HerpDerpPlugin", )
        plugin_info.extend(generate_plugin_info_list("JankyPlugin1",
                           version=self.v1))
        plugin_info.extend(generate_plugin_info_list("JankyPlugin2",
                           version=self.v2))

        self.addDetail("plugin_info", text_content(str(plugin_info)))
        self.registry = ModuleRegistry(config, plugin_info)

    def tearDown(self):
        super(ModuleRegistryPluginInfoTestsWithScenarios, self).tearDown()

    def test_get_plugin_info_dict(self):
        """
        The goal of this test is to validate that the plugin_info returned by
        ModuleRegistry.get_plugin_info is a dictionary whose key 'longName' is
        the same value as the string argument passed to
        ModuleRegistry.get_plugin_info.
        """
        plugin_name = "JankyPlugin1"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info['longName'], plugin_name)

    def test_get_plugin_info_dict_no_plugin(self):
        """
        The goal of this test case is to validate the behavior of
        ModuleRegistry.get_plugin_info when the given plugin cannot be found in
        ModuleRegistry's internal representation of the plugins_info.
        """
        plugin_name = "JunkyPlugin"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info, {})

    def test_get_plugin_info_dict_no_version(self):
        """
        The goal of this test case is to validate the behavior of
        ModuleRegistry.get_plugin_info when the given plugin longName returns a
        plugin_info dict that has no version string. In a sane world where
        plugin frameworks like Jenkins' are sane this should never happen, but
        I am including this test and the corresponding default behavior
        because, well, it's Jenkins.
        """
        plugin_name = "HerpDerpPlugin"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info['longName'], plugin_name)
        self.assertEqual(plugin_info['version'], (0,))

    def test_version_is_tuple(self):
        """
        The goal of this test case is to validate that the version string in
        the plugins_info list passed to ModulesRegistry is always converted to
        a tuple.
        """
        plugin_name = "JankyPlugin1"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        self.assertIsInstance(plugin_info['version'], tuple)

    def test_valid_version_tuple_comparisons(self):
        """
        The goal of this test case is to validate that valid tuple versions are
        ordinally correct. That is, for each given scenario, v1.op(v2)==True
        where 'op' is the equality operator defined for the scenario.
        """
        plugin_info1 = self.registry.get_plugin_info("JankyPlugin1")
        version1 = plugin_info1['version']
        self.addDetail('plugin_info1', text_content(str(plugin_info1)))

        plugin_info2 = self.registry.get_plugin_info("JankyPlugin2")
        version2 = plugin_info2['version']
        self.addDetail('plugin_info2', text_content(str(plugin_info2)))

        op = getattr(version1, self.op)

        self.assertTrue(op(version2), msg="Inexpectedly found {0} {1} {2} == "
                                          "False, when comparing versions!"
                                          .format(version1, self.op, version2))
