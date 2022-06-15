# Joint copyright:
#  - Copyright 2014 Hewlett-Packard Development Company, L.P.
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
from tests.enum_scenarios import scenario_list


fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture(
    params=scenario_list(fixtures_dir),
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


def test_yaml_snippet(scenario, check_job):
    if scenario.in_path.name.startswith("exception_"):
        with pytest.raises(JenkinsJobsException) as excinfo:
            check_job()
        assert str(excinfo.value).startswith("Duplicate ")
    else:
        check_job()
