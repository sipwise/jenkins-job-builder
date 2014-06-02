import os
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import ConfigParser
import cStringIO
import subprocess
import codecs
from jenkins_jobs import cmd


class CmdTests(unittest.TestCase):

    fixtures_path = os.path.abspath(__file__).rsplit(os.path.sep, 1)[0]+'/fixtures'
    tools_path = os.path.abspath(__file__).rsplit(os.path.sep, 3)[0]+'/tools'
    parser = cmd.create_parser()

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_non_existing_config_dir(self):
        """
        Run test mode and pass a non-existing configuration directory
        """
        args = self.parser.parse_args(['test', 'foo'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        with self.assertRaises(IOError):
            cmd.execute(args, config)

    def test_non_existing_config_file(self):
        """
        Run test mode and pass a non-existing configuration file
        """
        args = self.parser.parse_args(['test', 'foo.yaml'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        with self.assertRaises(IOError):
            cmd.execute(args, config)

    def test_non_existing_job(self):
        """
        Run test mode and pass a non-existing job name
        """
        args = self.parser.parse_args(['test', self.fixtures_path+'/cmd-001.yaml', 'invalid'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)   # should probably fail instead of no message

    def test_valid_job(self):
        """
        Run test mode and pass a valid job name
        """
        args = self.parser.parse_args(['test', self.fixtures_path+'/cmd-001.yaml', 'foo-job'])
        config = ConfigParser.ConfigParser()
        config.readfp(cStringIO.StringIO(cmd.DEFAULT_CONF))
        cmd.execute(args, config)

    def test_console_output(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """
        command = 'python '+self.tools_path+'/jenkins-jobs.py'+' test '+self.fixtures_path+'/cmd-001.yaml'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        console_out = unicode(process.communicate()[0], "utf-8")
        xml_content = u"%s" % codecs.open(self.fixtures_path+'/cmd-001.xml', 'r', 'utf-8').read()
        self.assertEqual(console_out, xml_content)

