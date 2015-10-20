import os
from jenkins_jobs import cmd
from six.moves import StringIO
from tests.base import mock
from testtools import TestCase

class TestCaseModuleConfig(TestCase):

    def open_config(path):
        def config = ""

        if path == '/etc/jenkins_jobs/jenkins_jobs.ini':
            SYSTEM_CONFIG = """
            [job_builder]
            config_scope=system
            """
            config = SYSTEM_CONFIG

        if path == os.path.join(os.path.expanduser('~'), '.config',
                                'jenkins_jobs', 'jenkins_jobs.ini'):
            USER_CONFIG = """
            [job_builder]
            config_scope=user
            """
            config = USER_CONFIG

        return StringIO(config)

    @mock.patch('os.path.isfile', return_value=True)
    def test_user_config_has_precedence(self):
        m = mock.MagicMock(side_effect=open_config)
        with mock.patch('__builtin__.open', m):
            config = cmd.setup_config_settings()
            self.assertEqual(config.get('job_builder', 'config_scope'),
                             'user')
