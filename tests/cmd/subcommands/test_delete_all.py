#  - Copyright 2016 Hewlett-Packard Development Company, L.P.
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

# The goal of these tests is to check that given a particular set of flags to
# Jenkins Job Builder's command line tools it will result in a particular set
# of actions by the JJB library, usually through interaction with the
# python-jenkins library.

import pytest


def test_delete_all_accept(mocker, default_config_file, execute_jenkins_jobs):
    """
    Test handling the deletion of a single Jenkins job.
    """

    mocker.patch("jenkins_jobs.cli.subcommand.base.JenkinsManager.delete_all_jobs")
    mocker.patch("jenkins_jobs.builder.JenkinsManager.get_views", return_value=[None])
    mocker.patch("jenkins_jobs.utils.input", return_value="y")

    args = ["--conf", default_config_file, "delete-all"]
    execute_jenkins_jobs(args)


def test_delete_all_abort(mocker, default_config_file, execute_jenkins_jobs):
    """
    Test handling the deletion of a single Jenkins job.
    """

    mocker.patch("jenkins_jobs.cli.subcommand.base.JenkinsManager.delete_all_jobs")
    mocker.patch("jenkins_jobs.utils.input", return_value="n")

    args = ["--conf", default_config_file, "delete-all"]
    with pytest.raises(SystemExit):
        execute_jenkins_jobs(args)


def test_delete_all_forced(mocker, default_config_file, execute_jenkins_jobs):
    """
    Test handling the deletion of a job and a view with --force flag.
    """

    delete_jobs = mocker.patch(
        "jenkins_jobs.cli.subcommand.base.JenkinsManager.delete_all_jobs"
    )
    delete_views = mocker.patch(
        "jenkins_jobs.cli.subcommand.base.JenkinsManager.delete_all_views"
    )
    get_jobs = mocker.patch("jenkins_jobs.builder.jenkins.Jenkins.get_all_jobs")
    get_jobs.return_value = [{"name": name} for name in ["job-1"]]
    get_views = mocker.patch("jenkins_jobs.builder.jenkins.Jenkins.get_views")
    get_views.return_value = [{"name": name} for name in ["view-1"]]
    input_mock = mocker.patch("jenkins_jobs.utils.input", return_value="n")

    args = ["--conf", default_config_file, "delete-all", "--force"]
    execute_jenkins_jobs(args)

    input_mock.assert_not_called()

    assert delete_jobs.call_count == 1
    assert delete_views.call_count == 1
