#
#  - Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

import os.path

import pytest

import jenkins_jobs


# Override fixture - do not use this mock.
@pytest.fixture(autouse=True)
def job_cache_mocked(mocker):
    pass


def test_save_on_exit(mocker):
    """
    Test that the cache is saved on normal object deletion
    """
    mocker.patch("jenkins_jobs.builder.JobCache.get_cache_dir", lambda x: "/bad/file")

    save_mock = mocker.patch("jenkins_jobs.builder.JobCache.save")
    mocker.patch("os.path.isfile", return_value=False)
    mocker.patch("jenkins_jobs.builder.JobCache._lock")
    jenkins_jobs.builder.JobCache("dummy")
    save_mock.assert_called_with()


def test_cache_file(mocker):
    """
    Test providing a cachefile.
    """
    mocker.patch("jenkins_jobs.builder.JobCache.get_cache_dir", lambda x: "/bad/file")

    test_file = os.path.abspath(__file__)
    mocker.patch("os.path.join", return_value=test_file)
    mocker.patch("yaml.safe_load")
    mocker.patch("jenkins_jobs.builder.JobCache._lock")
    jenkins_jobs.builder.JobCache("dummy").data = None
