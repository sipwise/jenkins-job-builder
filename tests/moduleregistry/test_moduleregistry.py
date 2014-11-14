import testtools as tt
from testtools.content import text_content
from testscenarios.testcase import TestWithScenarios
from six.moves import configparser, StringIO

from jenkins_jobs import cmd, errors
from jenkins_jobs.builder import ModuleRegistry


def generate_plugin_info_list(plugin_name, **kwargs):
    return [dict(longName=plugin_name, **kwargs),
            ]


class ModuleRegistryPluginInfoTestsWithScenarios(TestWithScenarios,
                                                 tt.TestCase):
    scenarios = [
        # cmp_result = 1 means v1 > v2
        # cmp_result = 0 means v1 == v2
        # cmp_result = -1 means v1 < v2
        ('s1', dict(v1='1.0.0', cmp_result=1, v2='0.8.0')),
        ('s2', dict(v1='1.0.1alpha', cmp_result=1, v2='1.0.0')),
        ('s3', dict(v1='1.0', cmp_result=0, v2='1.0.0')),
        ('s4', dict(v1='1.0', cmp_result=0, v2='1.0')),
        ('s5', dict(v1='1.0', cmp_result=-1, v2='1.8.0')),
        ('s6', dict(v1='1.0.1alpha', cmp_result=-1, v2='1.0.1')),
        ('s7', dict(v1='1.0alpha', cmp_result=-1, v2='1.0.0')),
    ]

    def setUp(self):
        super(ModuleRegistryPluginInfoTestsWithScenarios, self).setUp()

        config = configparser.ConfigParser()
        config.readfp(StringIO(cmd.DEFAULT_CONF))

        plugin_info = generate_plugin_info_list("HerpDerpPlugin", )
        plugin_info.extend(generate_plugin_info_list("JankyPlugin1",
                           version=self.v1))

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
        self.assertEqual(plugin_info['version'], '0')

    def test_cmp_plugin_version(self):
        """
        The goal of this test case is to validate that valid tuple versions are
        ordinally correct. That is, for each given scenario, v1.op(v2)==True
        where 'op' is the equality operator defined for the scenario.
        """
        plugin_name = "JankyPlugin1"
        plugin_info = self.registry.get_plugin_info(plugin_name)

        test = self.registry.cmp_plugin_version(plugin_name,
                                                self.v2) == self.cmp_result
        self.assertTrue(test,
                        msg="Unexpectedly found cmp({0}, {1}) != {2} "
                            "when comparing versions!"
                            .format(plugin_info['version'], self.v2,
                                    self.cmp_result))

    def test_cmp_plugin_version_nonexistent_plugin(self):
        """
        The goal of this test case is to validate that
        ModuleRegistry.cmp_plugin_version will raise PluginInfoError if passed
        a plugin_long_name for a plugin whose information is not available to
        the ModuleRegistry instance.
        """
        plugin_name = "DoesNotExistPlugin"
        with tt.ExpectedException(errors.PluginInfoError,
                                  "Plugin information not found for '{0}'"
                                  .format(plugin_name)):
            self.registry.cmp_plugin_version(plugin_name, self.v2)
