import os
from six.moves import configparser, StringIO
import mock
import testtools
from jenkins_jobs import cmd


class CmdTestsBase(testtools.TestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    parser = cmd.create_parser()

    def setUp(self):
        super(CmdTestsBase, self).setUp()
        self.config = configparser.ConfigParser()
        self.config.readfp(StringIO(cmd.DEFAULT_CONF))


class CmdTests(CmdTestsBase):

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with mock.patch('sys.stderr'):
            self.assertRaises(SystemExit, cmd.main, [])
