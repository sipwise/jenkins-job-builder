import io
from pathlib import Path

import pytest

from jenkins_jobs.cli import entry
from jenkins_jobs import builder


global_conf = "/etc/jenkins_jobs/jenkins_jobs.ini"
user_conf = Path.home() / ".config" / "jenkins_jobs" / "jenkins_jobs.ini"
local_conf = Path(__file__).parent / "jenkins_jobs.ini"


def test_use_global_config(mocker, default_config_file):
    """
    Verify that JJB uses the global config file by default
    """
    mocker.patch("jenkins_jobs.builder.JenkinsManager.get_plugins_info")

    args = ["test", "foo"]

    default_io_open = io.open

    def io_open(file, *args, **kw):
        if file == global_conf:
            default_io_open(default_config_file, "r", encoding="utf-8")
        else:
            return default_io_open(file, *args, **kw)

    def isfile(path):
        if path == global_conf:
            return True
        return False

    mocker.patch("os.path.isfile", side_effect=isfile)
    mocked_open = mocker.patch("io.open", side_effect=io_open)

    entry.JenkinsJobs(args, config_file_required=True)

    mocked_open.assert_called_with(global_conf, "r", encoding="utf-8")


def test_use_config_in_user_home(mocker, default_config_file):
    """
    Verify that JJB uses config file in user home folder
    """

    args = ["test", "foo"]

    default_io_open = io.open

    def io_open(file, *args, **kw):
        if file == str(user_conf):
            default_io_open(default_config_file, "r", encoding="utf-8")
        else:
            return default_io_open(file, *args, **kw)

    def isfile(path):
        if path == str(user_conf):
            return True
        return False

    mocker.patch("os.path.isfile", side_effect=isfile)
    mocked_open = mocker.patch("io.open", side_effect=io_open)

    entry.JenkinsJobs(args, config_file_required=True)
    mocked_open.assert_called_with(str(user_conf), "r", encoding="utf-8")


def test_non_existing_config_dir(default_config_file):
    """
    Run test mode and pass a non-existing configuration directory
    """
    args = ["--conf", default_config_file, "test", "foo"]
    jenkins_jobs = entry.JenkinsJobs(args)
    with pytest.raises(IOError):
        jenkins_jobs.execute()


def test_non_existing_config_file(default_config_file):
    """
    Run test mode and pass a non-existing configuration file
    """
    args = ["--conf", default_config_file, "test", "non-existing.yaml"]
    jenkins_jobs = entry.JenkinsJobs(args)
    with pytest.raises(IOError):
        jenkins_jobs.execute()


def test_config_options_not_replaced_by_cli_defaults(fixtures_dir):
    """
    Run test mode and check config settings from conf file retained
    when none of the global CLI options are set.
    """
    config_file = fixtures_dir / "settings_from_config.ini"
    args = ["--conf", str(config_file), "test", "dummy.yaml"]
    jenkins_jobs = entry.JenkinsJobs(args)
    jjb_config = jenkins_jobs.jjb_config
    assert jjb_config.jenkins["user"] == "jenkins_user"
    assert jjb_config.jenkins["password"] == "jenkins_password"
    assert jjb_config.builder["ignore_cache"]
    assert jjb_config.builder["flush_cache"]
    assert jjb_config.builder["update"] == "all"
    assert jjb_config.yamlparser["allow_empty_variables"]


def test_config_options_overriden_by_cli():
    """
    Run test mode and check config settings from conf file retained
    when none of the global CLI options are set.
    """
    args = [
        "--user",
        "myuser",
        "--password",
        "mypassword",
        "--ignore-cache",
        "--flush-cache",
        "--allow-empty-variables",
        "test",
        "dummy.yaml",
    ]
    jenkins_jobs = entry.JenkinsJobs(args)
    jjb_config = jenkins_jobs.jjb_config
    assert jjb_config.jenkins["user"] == "myuser"
    assert jjb_config.jenkins["password"] == "mypassword"
    assert jjb_config.builder["ignore_cache"]
    assert jjb_config.builder["flush_cache"]
    assert jjb_config.yamlparser["allow_empty_variables"]


def test_update_timeout_not_set(mocker, fixtures_dir, default_config_file):
    """Check that timeout is left unset

    Test that the Jenkins object has the timeout set on it only when
    provided via the config option.
    """
    jenkins_mock = mocker.patch("jenkins_jobs.cli.subcommand.base.JenkinsManager")

    path = fixtures_dir / "cmd-002.yaml"
    args = ["--conf", default_config_file, "update", str(path)]

    jenkins_mock.return_value.update_jobs.return_value = ([], 0)
    jenkins_mock.return_value.update_views.return_value = ([], 0)
    jenkins_jobs = entry.JenkinsJobs(args)
    jenkins_jobs.execute()

    # validate that the JJBConfig used to initialize builder.Jenkins
    # contains the expected timeout value.

    jjb_config = jenkins_mock.call_args[0][0]
    assert jjb_config.jenkins["timeout"] == builder._DEFAULT_TIMEOUT


def test_update_timeout_set(mocker, fixtures_dir):
    """Check that timeout is set correctly

    Test that the Jenkins object has the timeout set on it only when
    provided via the config option.
    """
    jenkins_mock = mocker.patch("jenkins_jobs.cli.subcommand.base.JenkinsManager")

    path = fixtures_dir / "cmd-002.yaml"
    config_file = fixtures_dir / "non-default-timeout.ini"
    args = ["--conf", str(config_file), "update", str(path)]

    jenkins_mock.return_value.update_jobs.return_value = ([], 0)
    jenkins_mock.return_value.update_views.return_value = ([], 0)
    jenkins_jobs = entry.JenkinsJobs(args)
    jenkins_jobs.execute()

    # validate that the JJBConfig used to initialize builder.Jenkins
    # contains the expected timeout value.

    jjb_config = jenkins_mock.call_args[0][0]
    assert jjb_config.jenkins["timeout"] == 0.2
