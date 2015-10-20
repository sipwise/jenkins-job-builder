from jenkins_jobs import cmd
from tests.base import BaseTestCase

class TestCaseModuleConfig(BaseTestCase):
    def setUp(self):
        super(TestCaseModuleConfig, self).setUp()
        self.useFixture(fixtures.TempHomeDir())

    def test_user_config_has_precedence(self)
        cmd.setup_config_settings()
