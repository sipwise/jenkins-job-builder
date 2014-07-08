import os
import ConfigParser
import cStringIO
import codecs
import mock
import testtools
from jenkins_jobs import cmd


class CmdTests(testtools.TestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    parser = cmd.create_parser()

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with mock.patch('sys.stderr'):
            self.assertRaises(SystemExit, self.parser.parse_args, [])

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = self.parser.parse_args(['test', 'foo'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        self.assertRaises(IOError, cmd.execute, args, config)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = self.parser.parse_args(['test', 'non-existing.yaml'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        self.assertRaises(IOError, cmd.execute, args, config)

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
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)   # probably better to fail here

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = self.parser.parse_args(['test',
                                       os.path.join(self.fixtures_path,
                                                    'cmd-001.yaml'),
                                       'foo-job'])
        args.output_dir = mock.MagicMock()
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)   # probably better to fail here

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        console_out = cStringIO.StringIO()
        with mock.patch('sys.stdout', console_out):
            cmd.main(['test', os.path.join(self.fixtures_path,
                      'cmd-001.yaml')])
        xml_content = u"%s" % codecs.open(os.path.join(self.fixtures_path,
                                                       'cmd-001.xml'),
                                          'r',
                                          'utf-8').read()
        self.assertEqual(console_out.getvalue(), xml_content)

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
