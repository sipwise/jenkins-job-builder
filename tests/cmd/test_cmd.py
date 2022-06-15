import pytest

from jenkins_jobs.cli import entry


def test_with_empty_args(mocker):
    """
    User passes no args, should fail with SystemExit
    """
    with pytest.raises(SystemExit):
        entry.JenkinsJobs([])
