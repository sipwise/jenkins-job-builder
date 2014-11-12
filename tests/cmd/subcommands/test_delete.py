import mock
from jenkins_jobs import cmd
from tests.cmd.test_cmd import CmdTestsBase


class DeleteTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.cmd.Builder.delete_job')
    def test_delete_single_job(self, delete_job_mock):
        """
        Test handling the deletion of a single Jenkins job.
        """

        args = self.parser.parse_args(['delete', 'test_job'])
        cmd.execute(args, self.config)  # passes if executed without error

    @mock.patch('jenkins_jobs.cmd.Builder.delete_job')
    def test_delete_multiple_jobs(self, delete_job_mock):
        """
        Test handling the deletion of multiple Jenkins jobs.
        """

        args = self.parser.parse_args(['delete', 'test_job1', 'test_job2'])
        cmd.execute(args, self.config)  # passes if executed without error
