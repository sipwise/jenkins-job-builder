import fixtures
from jenkins_jobs import cmd
from tests.base import BaseTestCase


class TestCaseModuleConfig(BaseTestCase):

    def setUp(self):
        super(TestCaseModuleConfig, self).setUp()
        self.useFixture(fixtures.TempHomeDir())

        SYSTEM_CONFIG = """
        [job_builder]
        is_system_config=True
        """
        system_ini = '/etc/jenkins_jobs/jenkins_jobs.ini'
        system_config = io.open(system_ini, 'w', encoding='utf-8')
        system_config.write(SYSTEM_CONFIG)
        system_config.close()

    def test_user_config_has_precedence(self):
        config = cmd.setup_config_settings()
        self.assertTrue(options.ignore_cache)

        USER_CONFIG = """
        [job_builder]
        is_system_config=False
        """
        user_ini = os.path.join(os.path.expanduser('~'), '.config',
                                'jenkins_jobs', 'jenkins_jobs.ini')
        user_config = io.open(user_ini, 'w', encoding='utf-8')
        user_config.write(USER_CONFIG)
        user_config.close()

        config = cmd.setup_config_settings()
        self.assertFalse(options.ignore_cache)
