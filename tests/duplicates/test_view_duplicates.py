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


def test_yaml_snippet(scenario, expected_error, check_view):
    if scenario.error_path.exists():
        with pytest.raises(JenkinsJobsException) as excinfo:
            check_view()
        error = "\n".join(excinfo.value.lines)
        print()
        print(error)
        assert error.replace(str(fixtures_dir) + "/", "") == expected_error
    else:
        check_view()
