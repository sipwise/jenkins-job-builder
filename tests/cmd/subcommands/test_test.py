import os
import io
import codecs
import mock
from jenkins_jobs import cmd
from tests.cmd.test_cmd import CmdTestsBase
import tests.utils.mocks as jjb_mocks


# Testing the cmd module can sometimes result in the CacheStorage class
# attempting to create the cache directory multiple times as the tests
# are run in parallel.  Stub out the CacheStorage to ensure that each
# test can safely create the cache directory without risk of interference.
@mock.patch('jenkins_jobs.builder.CacheStorage', mock.MagicMock)
@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class TestTests(CmdTestsBase):

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = self.parser.parse_args(['test', 'foo'])
        self.assertRaises(IOError, cmd.execute, args, self.config)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = self.parser.parse_args(['test', 'non-existing.yaml'])
        self.assertRaises(IOError, cmd.execute, args, self.config)

    def test_non_existing_job(self):
        """
        Run test mode and pass a non-existing job name
        (probably better to fail here)
        """
        args = self.parser.parse_args(['test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'invalid'])
        args.output_dir = mock.MagicMock()
        cmd.execute(args, self.config)   # probably better to fail here

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = self.parser.parse_args(['test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'foo-job'])
        args.output_dir = mock.MagicMock()
        cmd.execute(args, self.config)   # probably better to fail here

    def test_plugins_info_option(self):
        """
        Run test mode and passing a valid plugins_info YAML file.
        """
        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            cmd.main(['--conf',
                      os.path.join(self.fixtures_path,
                                   'cmd-002.conf'),
                      'test',
                      '-p',
                      os.path.join(self.fixtures_path,
                                   'cmd-002.plugins-info.yaml'),
                      os.path.join(self.fixtures_path,
                                   'cmd-002.yaml')])

        xml_content = codecs.open(os.path.join(self.fixtures_path,
                                               'cmd-002.xml'),
                                  'r', 'utf-8').read()
        self.assertEqual(console_out.getvalue().decode('utf-8'), xml_content)

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    def test_multi_path(self, update_job_mock):
        """
        Run test mode and pass multiple paths.
        """
        path_list = jjb_mocks.os_walk_return_values.keys()
        multipath = os.pathsep.join(path_list)

        args = self.parser.parse_args(['test', multipath])
        args.output_dir = mock.MagicMock()

        cmd.execute(args, self.config)
        self.assertEqual(args.path, path_list)
        update_job_mock.assert_called_with(path_list, [],
                                           output=args.output_dir)

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.walk')
    def test_recursive_multi_path(self, os_walk_mock, isdir_mock,
                                  update_job_mock):
        """
        Run test mode and pass multiple paths with recursive path option.
        """

        os_walk_mock.side_effect = jjb_mocks.os_walk_side_effects
        isdir_mock.return_value = True

        path_list = jjb_mocks.os_walk_return_values.keys()
        paths = []
        for path in path_list:
            paths.extend([p for p, _, _ in jjb_mocks.os_walk_return_values[path]])

        multipath = os.pathsep.join(path_list)

        args = self.parser.parse_args(['test', '-r', multipath])
        args.output_dir = mock.MagicMock()

        cmd.execute(args, self.config)

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)

        args = self.parser.parse_args(['test', multipath])
        self.config.set('job_builder', 'recursive', 'True')
        cmd.execute(args, self.config)

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            cmd.main(['test', os.path.join(self.fixtures_path,
                      'cmd-001.yaml')])
        xml_content = codecs.open(os.path.join(self.fixtures_path,
                                               'cmd-001.xml'),
                                  'r', 'utf-8').read()
        self.assertEqual(console_out.getvalue().decode('utf-8'), xml_content)

    def test_config_with_test(self):
        """
        Run test mode and pass a config file
        """
        args = self.parser.parse_args(['--conf',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.conf'),
                                       'test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'foo-job'])
        config = cmd.setup_config_settings(args)
        self.assertEqual(config.get('jenkins', 'url'),
                         "http://test-jenkins.with.non.default.url:8080/")

    @mock.patch('jenkins_jobs.cmd.Builder.update_job')
    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.walk')
    def test_recursive_path_option(self, os_walk_mock, isdir_mock,
                                   update_job_mock):
        """
        Test handling of recursive path option
        """

        os_walk_mock.return_value = [
            ('/jjb_configs', ('dir1', 'dir2', 'dir3'), ()),
            ('/jjb_configs/dir1', ('bar',), ()),
            ('/jjb_configs/dir2', ('baz',), ()),
            ('/jjb_configs/dir3', (), ()),
            ('/jjb_configs/dir1/bar', (), ()),
            ('/jjb_configs/dir2/baz', (), ()),
        ]
        isdir_mock.return_value = True
        paths = [path for path, _, _ in os_walk_mock.return_value]

        args = self.parser.parse_args(['test', '-r', '/jjb_configs'])
        args.output_dir = mock.MagicMock()
        cmd.execute(args, self.config)   # probably better to fail here

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)

        args = self.parser.parse_args(['test', '/jjb_configs'])
        self.config.set('job_builder', 'recursive', 'True')
        cmd.execute(args, self.config)   # probably better to fail here

        update_job_mock.assert_called_with(paths, [], output=args.output_dir)
