from operator import attrgetter
from pathlib import Path

import pytest

from jenkins_jobs.errors import JenkinsJobsException
from tests.enum_scenarios import scenario_list


fixtures_dir = Path(__file__).parent / "view_fixtures"


@pytest.fixture(
    params=scenario_list(fixtures_dir),
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


def test_yaml_snippet(scenario, check_view):
    if scenario.in_path.name.startswith("exception_"):
        with pytest.raises(JenkinsJobsException) as excinfo:
            check_view()
        assert str(excinfo.value).startswith("Duplicate ")
    else:
        check_view()
