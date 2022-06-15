from pathlib import Path

import pytest

from jenkins_jobs.cli import entry


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def default_config_file(fixtures_dir):
    return str(fixtures_dir / "empty_builder.ini")


@pytest.fixture
def execute_jenkins_jobs():
    def execute(args):
        jenkins_jobs = entry.JenkinsJobs(args)
        jenkins_jobs.execute()

    return execute
