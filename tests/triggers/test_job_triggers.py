from operator import attrgetter
from pathlib import Path

import pytest

from tests.enum_scenarios import scenario_list


fixtures_dir = Path(__file__).parent / "job_fixtures"


@pytest.fixture(
    params=scenario_list(fixtures_dir),
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


def test_job(check_job):
    check_job()
