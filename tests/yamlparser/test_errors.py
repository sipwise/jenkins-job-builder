# Joint copyright:
#  - Copyright 2012,2013 Wikimedia Foundation
#  - Copyright 2012,2013 Antoine "hashar" Musso
#  - Copyright 2013 Arnaud Fabre
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
from operator import attrgetter
from pathlib import Path

import pytest

from jenkins_jobs.errors import JenkinsJobsException
from tests.enum_scenarios import scenario_list

fixtures_dir = Path(__file__).parent / "error_fixtures"


@pytest.fixture(
    params=scenario_list(fixtures_dir),
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


# Override to avoid scenarios usage.
@pytest.fixture
def config_path():
    return os.devnull


# Override to avoid scenarios usage.
@pytest.fixture
def plugins_info():
    return None


def test_error(check_parser, scenario, expected_error):
    with pytest.raises(JenkinsJobsException) as excinfo:
        check_parser(scenario.in_path)
    error = "\n".join(excinfo.value.lines)
    print()
    print(error)
    canonical_error = error.replace(str(fixtures_dir) + "/", "").replace(
        str(fixtures_dir), "fixtures-dir"
    )
    assert canonical_error == expected_error
