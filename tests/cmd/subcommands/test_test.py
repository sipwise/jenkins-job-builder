import io
import os
import yaml

import jenkins

from jenkins_jobs.cli import entry
from jenkins_jobs import cmd
from jenkins_jobs.errors import JenkinsJobsException
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase
from tests.cmd.test_recurse_path import fake_os_walk


os_walk_return_values = {
    '/jjb_projects': [
        ('/jjb_projects', (['dir1', 'dir2', 'dir3'], ())),
        ('/jjb_projects/dir1', (['bar'], ())),
        ('/jjb_projects/dir2', (['baz'], ())),
        ('/jjb_projects/dir3', ([], ())),
        ('/jjb_projects/dir1/bar', ([], ())),
        ('/jjb_projects/dir2/baz', ([], ())),
    ],
    '/jjb_templates': [
        ('/jjb_templates', (['dir1', 'dir2', 'dir3'], ())),
        ('/jjb_templates/dir1', (['bar'], ())),
        ('/jjb_templates/dir2', (['baz'], ())),
        ('/jjb_templates/dir3', ([], ())),
        ('/jjb_templates/dir1/bar', ([], ())),
        ('/jjb_templates/dir2/baz', ([], ())),
    ],
    '/jjb_macros': [
        ('/jjb_macros', (['dir1', 'dir2', 'dir3'], ())),
        ('/jjb_macros/dir1', (['bar'], ())),
        ('/jjb_macros/dir2', (['baz'], ())),
        ('/jjb_macros/dir3', ([], ())),
        ('/jjb_macros/dir1/bar', ([], ())),
        ('/jjb_macros/dir2/baz', ([], ())),
    ],
}


def os_walk_side_effects(path_name, topdown):
    return fake_os_walk(os_walk_return_values[path_name])(path_name, topdown)


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class TestTests(CmdTestsBase):

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = ['--conf', self.default_config_file, 'test', 'foo']
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        self.assertRaises(IOError, jenkins_jobs.execute)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = ['--conf', self.default_config_file, 'test',
                'non-existing.yaml']
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        self.assertRaises(IOError, jenkins_jobs.execute)

    def test_non_existing_job(self):
        """
        Run test mode and pass a non-existing job name
        (probably better to fail here)
        """
        args = ['--conf', self.default_config_file, 'test',
                os.path.join(self.fixtures_path,
                             'cmd-001.yaml'),
                'invalid']
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        jenkins_jobs.execute()

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = ['--conf', self.default_config_file, 'test',
                os.path.join(self.fixtures_path,
                             'cmd-001.yaml'),
                'foo-job']
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.Mock(wraps=io.BytesIO())
        jenkins_jobs.execute()

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    def test_multi_path(self, update_job_mock):
        """
        Run test mode and pass multiple paths.
        """
        path_list = list(os_walk_return_values.keys())
        multipath = os.pathsep.join(path_list)

        args = ['--conf', self.default_config_file, 'test', multipath]

        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        jenkins_jobs.execute()
        self.assertEqual(jenkins_jobs.options.path, path_list)
        update_job_mock.assert_called_with(
            path_list, [], output=jenkins_jobs.options.output_dir)

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.walk')
    def test_recursive_multi_path(self, os_walk_mock, isdir_mock,
                                  update_job_mock):
        """
        Run test mode and pass multiple paths with recursive path option.
        """

        os_walk_mock.side_effect = os_walk_side_effects
        isdir_mock.return_value = True

        path_list = os_walk_return_values.keys()
        paths = []
        for path in path_list:
            paths.extend([p for p, _ in os_walk_return_values[path]])

        multipath = os.pathsep.join(path_list)

        args = ['--conf', self.default_config_file, 'test', '-r', multipath]

        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        jenkins_jobs.execute()

        update_job_mock.assert_called_with(
            paths, [], output=jenkins_jobs.options.output_dir)

        args = ['--conf', self.default_config_file, 'test', multipath]
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        jenkins_jobs.config_file_values.set('job_builder', 'recursive', 'True')
        jenkins_jobs.execute()

        update_job_mock.assert_called_with(
            paths, [], output=jenkins_jobs.options.output_dir)

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.walk')
    def test_recursive_multi_path_with_excludes(self, os_walk_mock, isdir_mock,
                                                update_job_mock):
        """
        Run test mode and pass multiple paths with recursive path option.
        """

        os_walk_mock.side_effect = os_walk_side_effects
        isdir_mock.return_value = True

        path_list = os_walk_return_values.keys()
        paths = []
        for path in path_list:
            paths.extend([p for p, __ in os_walk_return_values[path]
                          if 'dir1' not in p and 'dir2' not in p])

        multipath = os.pathsep.join(path_list)

        args = ['--conf', self.default_config_file, 'test', '-r', multipath,
                '-x', 'dir1:dir2']

        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.options.output_dir = mock.MagicMock()
        jenkins_jobs.execute()

        update_job_mock.assert_called_with(
            paths, [], output=jenkins_jobs.options.output_dir)

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            args = ['--conf', self.default_config_file, 'test',
                    os.path.join(self.fixtures_path, 'cmd-001.yaml')]
            jenkins_jobs = entry.JenkinsJobs(args)
            jenkins_jobs.execute()
        xml_content = io.open(os.path.join(self.fixtures_path, 'cmd-001.xml'),
                              'r', encoding='utf-8').read()
        self.assertEqual(console_out.getvalue().decode('utf-8'), xml_content)

    def test_stream_input_output_utf8_encoding(self):
        """
        Run test mode simulating using pipes for input and output using
        utf-8 encoding
        """
        console_out = io.BytesIO()

        input_file = os.path.join(self.fixtures_path, 'cmd-001.yaml')
        with io.open(input_file, 'r') as f:
            with mock.patch('sys.stdout', console_out):
                with mock.patch('sys.stdin', f):
                    args = ['--conf', self.default_config_file, 'test']
                    jenkins_jobs = entry.JenkinsJobs(args)
                    jenkins_jobs.execute()

        xml_content = io.open(os.path.join(self.fixtures_path, 'cmd-001.xml'),
                              'r', encoding='utf-8').read()
        value = console_out.getvalue().decode('utf-8')
        self.assertEqual(value, xml_content)

    def test_stream_input_output_ascii_encoding(self):
        """
        Run test mode simulating using pipes for input and output using
        ascii encoding with unicode input
        """
        console_out = io.BytesIO()
        console_out.encoding = 'ascii'

        input_file = os.path.join(self.fixtures_path, 'cmd-001.yaml')
        with io.open(input_file, 'r') as f:
            with mock.patch('sys.stdout', console_out):
                with mock.patch('sys.stdin', f):
                    args = ['--conf', self.default_config_file, 'test']
                    jenkins_jobs = entry.JenkinsJobs(args)
                    jenkins_jobs.execute()

        xml_content = io.open(os.path.join(self.fixtures_path, 'cmd-001.xml'),
                              'r', encoding='utf-8').read()
        value = console_out.getvalue().decode('ascii')
        self.assertEqual(value, xml_content)

    def test_stream_output_ascii_encoding_invalid_char(self):
        """
        Run test mode simulating using pipes for input and output using
        ascii encoding for output with include containing a character
        that cannot be converted.
        """
        console_out = io.BytesIO()
        console_out.encoding = 'ascii'

        input_file = os.path.join(self.fixtures_path, 'unicode001.yaml')
        with io.open(input_file, 'r', encoding='utf-8') as f:
            with mock.patch('sys.stdout', console_out):
                with mock.patch('sys.stdin', f):
                    args = ['--conf', self.default_config_file, 'test']
                    jenkins_jobs = entry.JenkinsJobs(args)
                    e = self.assertRaises(UnicodeError, jenkins_jobs.execute)
        self.assertIn("'ascii' codec can't encode character", str(e))

    def test_config_with_test(self):
        """
        Run test mode and pass a config file
        """
        args = ['--conf',
                os.path.join(self.fixtures_path,
                             'cmd-001.conf'),
                'test',
                os.path.join(self.fixtures_path,
                             'cmd-001.yaml'),
                'foo-job']
        jenkins_jobs = entry.JenkinsJobs(args)
        config = cmd.setup_config_settings(jenkins_jobs.options)
        self.assertEqual(config.get('jenkins', 'url'),
                         "http://test-jenkins.with.non.default.url:8080/")

    @mock.patch('jenkins_jobs.builder.YamlParser.generateXML')
    @mock.patch('jenkins_jobs.parser.ModuleRegistry')
    def test_plugins_info_stub_option(self, registry_mock, generateXML_mock):
        """
        Test handling of plugins_info stub option.
        """
        plugins_info_stub_yaml_file = os.path.join(self.fixtures_path,
                                                   'plugins-info.yaml')
        args = ['--conf',
                os.path.join(self.fixtures_path, 'cmd-001.conf'),
                'test',
                '-p',
                plugins_info_stub_yaml_file,
                os.path.join(self.fixtures_path, 'cmd-001.yaml')]

        with mock.patch('sys.stdout'):
            jenkins_jobs = entry.JenkinsJobs(args)
            jenkins_jobs.execute()

        with io.open(plugins_info_stub_yaml_file,
                     'r', encoding='utf-8') as yaml_file:
            plugins_info_list = yaml.load(yaml_file)

        registry_mock.assert_called_with(jenkins_jobs.config_file_values,
                                         plugins_info_list)

    @mock.patch('jenkins_jobs.builder.YamlParser.generateXML')
    @mock.patch('jenkins_jobs.parser.ModuleRegistry')
    def test_bogus_plugins_info_stub_option(self, registry_mock,
                                            generateXML_mock):
        """
        Verify that a JenkinsJobException is raised if the plugins_info stub
        file does not yield a list as its top-level object.
        """
        plugins_info_stub_yaml_file = os.path.join(self.fixtures_path,
                                                   'bogus-plugins-info.yaml')
        args = ['--conf',
                os.path.join(self.fixtures_path, 'cmd-001.conf'),
                'test',
                '-p',
                plugins_info_stub_yaml_file,
                os.path.join(self.fixtures_path, 'cmd-001.yaml')]

        with mock.patch('sys.stdout'):
            jenkins_jobs = entry.JenkinsJobs(args)
            e = self.assertRaises(JenkinsJobsException, jenkins_jobs.execute)
        self.assertIn("must contain a Yaml list", str(e))


class TestJenkinsGetPluginInfoError(CmdTestsBase):
    """ This test class is used for testing the 'test' subcommand when we want
    to validate its behavior without mocking
    jenkins_jobs.builder.Jenkins.get_plugins_info
    """

    @mock.patch('jenkins.Jenkins.get_plugins_info')
    def test_console_output_jenkins_connection_failure_warning(
            self, get_plugins_info_mock):
        """
        Run test mode and verify that failed Jenkins connection attempt
        exception does not bubble out of cmd.main. Ideally, we would also test
        that an appropriate message is logged to stderr but it's somewhat
        difficult to figure out how to actually enable stderr in this test
        suite.
        """

        get_plugins_info_mock.side_effect = \
            jenkins.JenkinsException("Connection refused")
        with mock.patch('sys.stdout'):
            try:
                args = ['--conf', self.default_config_file, 'test',
                        os.path.join(self.fixtures_path, 'cmd-001.yaml')]
                jenkins_jobs = entry.JenkinsJobs(args)
                jenkins_jobs.execute()
            except jenkins.JenkinsException:
                self.fail("jenkins.JenkinsException propagated to main")
            except:
                pass  # only care about jenkins.JenkinsException for now

    @mock.patch('jenkins.Jenkins.get_plugins_info')
    def test_skip_plugin_retrieval_if_no_config_provided(
            self, get_plugins_info_mock):
        """
        Verify that retrieval of information from Jenkins instance about its
        plugins will be skipped when run if no config file provided.
        """
        with mock.patch('sys.stdout', new_callable=io.BytesIO):
            args = ['--conf', self.default_config_file, 'test',
                    os.path.join(self.fixtures_path, 'cmd-001.yaml')]
            entry.JenkinsJobs(args)
        self.assertFalse(get_plugins_info_mock.called)

    @mock.patch('jenkins.Jenkins.get_plugins_info')
    def test_skip_plugin_retrieval_if_disabled(self, get_plugins_info_mock):
        """
        Verify that retrieval of information from Jenkins instance about its
        plugins will be skipped when run if a config file provided and disables
        querying through a config option.
        """
        with mock.patch('sys.stdout', new_callable=io.BytesIO):
            args = ['--conf',
                    os.path.join(self.fixtures_path,
                                 'disable-query-plugins.conf'),
                    'test',
                    os.path.join(self.fixtures_path, 'cmd-001.yaml')]
            entry.JenkinsJobs(args)
        self.assertFalse(get_plugins_info_mock.called)
