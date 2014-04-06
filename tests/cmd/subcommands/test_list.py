import io
import os

from testscenarios.testcase import TestWithScenarios

from jenkins_jobs import cmd
from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class ListFromJenkinsTests(TestWithScenarios, CmdTestsBase):

    scenarios = [
        ('single',
            dict(jobs=['job1'], globs=[], found=['job1'])),
        ('multiple',
            dict(jobs=['job1', 'job2'], globs=[], found=['job1', 'job2'])),
        ('multiple_with_glob',
            dict(jobs=['job1', 'job2', 'job3'], globs=["job[1-2]"],
                 found=['job1', 'job2'])),
        ('multiple_with_multi_glob',
            dict(jobs=['job1', 'job2', 'job3', 'job4'],
                 globs=["job1", "job[24]"],
                 found=['job1', 'job2', 'job4'])),
    ]

    @mock.patch('jenkins_jobs.builder.Jenkins.get_jobs')
    def test_list(self, get_jobs_mock):

        def _get_jobs():
            return [{'name': name} for name in self.jobs]

        get_jobs_mock.side_effect = _get_jobs
        console_out = io.BytesIO()
        args = self.parser.parse_args(['list'] + self.globs)
        with mock.patch('sys.stdout', console_out):
            cmd.execute(args, self.config)

        self.assertEqual(console_out.getvalue().decode('utf-8').rstrip(),
                         ('\n'.join(self.found)))


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class ListFromYamlTests(TestWithScenarios, CmdTestsBase):

    scenarios = [
        ('all',
            dict(globs=[], found=['bar001', 'bar002', 'baz001', 'bam001'])),
        ('some',
            dict(globs=["*am*", "*002", "bar001"],
                 found=['bar001', 'bar002', 'bam001'])),
    ]

    def test_list(self):
        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            cmd.main(['list', '-p', path] + self.globs)

        self.assertEqual(console_out.getvalue().decode('utf-8').rstrip(),
                         ('\n'.join(self.found)))
