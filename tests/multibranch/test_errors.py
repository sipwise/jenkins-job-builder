#
# Copyright (c) 2018 Sorin Sbarnea <ssbarnea@users.noreply.github.com>
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
from operator import attrgetter
from pathlib import Path

import pytest

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.modules import project_multibranch
from tests.enum_scenarios import scenario_list

fixtures_dir = Path(__file__).parent / "error_fixtures"


@pytest.fixture(
    params=scenario_list(fixtures_dir),
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


def test_error(check_generator, expected_error):
    with pytest.raises(JenkinsJobsException) as excinfo:
        check_generator(project_multibranch.WorkflowMultiBranch)
    error = "\n".join(excinfo.value.lines)
    print()
    print(error)
    assert error.replace(str(fixtures_dir) + "/", "") == expected_error
