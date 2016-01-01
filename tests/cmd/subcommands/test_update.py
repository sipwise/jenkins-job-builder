
# Joint copyright:
#  - Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import six

from tests.base import mock
from tests.cmd.test_cmd import CmdTestsBase


@mock.patch('jenkins_jobs.builder.Jenkins.get_plugins_info', mock.MagicMock)
class UpdateTests(CmdTestsBase):

    @mock.patch('jenkins_jobs.cli.entry.Builder.update_jobs')
    def test_update_jobs(self, update_jobs_mock):
        """
        Test update_job is called
        """
        # don't care about the value returned here
        update_jobs_mock.return_value = ([], 0)

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', path]

        self.execute_jenkins_jobs_with_args(args)
        update_jobs_mock.assert_called_with([path], [], n_workers=mock.ANY)

    @mock.patch('jenkins_jobs.builder.Jenkins.is_job', return_value=True)
    @mock.patch('jenkins_jobs.builder.Jenkins.get_jobs')
    @mock.patch('jenkins_jobs.builder.Jenkins.get_job_md5')
    @mock.patch('jenkins_jobs.builder.Jenkins.update_job')
    def test_update_jobs_decode_job_output(self, update_job_mock,
                                           get_job_md5_mock, get_jobs_mock,
                                           is_job_mock):
        """
        Test that job xml output has been decoded before attempting to update
        """
        # don't care about the value returned here
        update_job_mock.return_value = ([], 0)

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', path]

        self.execute_jenkins_jobs_with_args(args)
        self.assertTrue(isinstance(update_job_mock.call_args[0][1],
                                   six.text_type))

    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.job_exists')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.get_jobs')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.reconfig_job')
    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins.delete_job')
    def test_update_jobs_and_delete_old(self,
                                        jenkins_delete_job,
                                        jenkins_reconfig_job,
                                        jenkins_get_jobs,
                                        jenkins_job_exists, ):
        """
        Test update behaviour with --delete-old option

        Test update of jobs with the --delete-old option enabled, where only
        some jobs result in has_changed() to limit the number of times
        update_job is called, and have the get_jobs() method return additional
        jobs not in the input yaml to test that the code in cmd will call
        delete_job() after update_job() when '--delete-old' is set but only
        for the extra jobs.
        """
        jobs = ['old_job001', 'old_job002']
        extra_jobs = [{'name': name} for name in jobs]

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', '--delete-old',
                path]

        jenkins_get_jobs.return_value = extra_jobs

        with mock.patch('jenkins_jobs.builder.Jenkins.is_managed',
                        return_value=True):
            self.execute_jenkins_jobs_with_args(args)

        jenkins_reconfig_job.assert_has_calls(
            [mock.call(job_name, mock.ANY)
             for job_name in ['bar001', 'bar002', 'baz001', 'bam001']],
            any_order=True
        )
        jenkins_delete_job.assert_has_calls([mock.call(job_name)
                                             for job_name in jobs])

    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins')
    def test_update_timeout_not_set(self, jenkins_mock):
        """Check that timeout is left unset

        Test that the Jenkins object has the timeout set on it only when
        provided via the config option.
        """

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        args = ['--conf', self.default_config_file, 'update', path]

        with mock.patch(
            'jenkins_jobs.cli.entry.Builder.update_job') as update_mock:
            update_mock.return_value = ([], 0)
            self.execute_jenkins_jobs_with_args(args)
        # unless the timeout is set, should only call with 3 arguments
        # (url, user, password)
        self.assertEquals(len(jenkins_mock.call_args[0]), 3)

    @mock.patch('jenkins_jobs.builder.jenkins.Jenkins')
    def test_update_timeout_set(self, jenkins_mock):
        """Check that timeout is set correctly

        Test that the Jenkins object has the timeout set on it only when
        provided via the config option.
        """

        path = os.path.join(self.fixtures_path, 'cmd-002.yaml')
        config_file = os.path.join(self.fixtures_path,
                                   'non-default-timeout.ini')
        args = ['--conf', config_file, 'update', path]

        with mock.patch(
            'jenkins_jobs.cli.entry.Builder.update_job') as update_mock:
            update_mock.return_value = ([], 0)
            self.execute_jenkins_jobs_with_args(args)
        # when timeout is set, the fourth argument to the Jenkins api init
        # should be the value specified from the config
        self.assertEquals(jenkins_mock.call_args[0][3], 0.2)
