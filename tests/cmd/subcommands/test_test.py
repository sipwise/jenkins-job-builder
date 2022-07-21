# Joint copyright:
#  - Copyright 2015 Hewlett-Packard Development Company, L.P.
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

# The goal of these tests is to check that given a particular set of flags to
# Jenkins Job Builder's command line tools it will result in a particular set
# of actions by the JJB library, usually through interaction with the
# python-jenkins library.

import filecmp
import io
import difflib
import os
import yaml
from unittest import mock

import jenkins
import pytest
from testtools.assertions import assert_that

from jenkins_jobs.cli import entry


def test_non_existing_job(fixtures_dir, default_config_file, execute_jenkins_jobs):
    """
    Run test mode and pass a non-existing job name
    (probably better to fail here)
    """
    args = [
        "--conf",
        default_config_file,
        "test",
        str(fixtures_dir / "cmd-001.yaml"),
        "invalid",
    ]
    execute_jenkins_jobs(args)


def test_valid_job(fixtures_dir, default_config_file, execute_jenkins_jobs):
    """
    Run test mode and pass a valid job name
    """
    args = [
        "--conf",
        default_config_file,
        "test",
        str(fixtures_dir / "cmd-001.yaml"),
        "foo-job",
    ]
    execute_jenkins_jobs(args)


def test_console_output(
    capsys, fixtures_dir, default_config_file, execute_jenkins_jobs
):
    """
    Run test mode and verify that resulting XML gets sent to the console.
    """

    args = [
        "--conf",
        default_config_file,
        "test",
        str(fixtures_dir / "cmd-001.yaml"),
    ]
    execute_jenkins_jobs(args)

    expected_output = fixtures_dir.joinpath("cmd-001.xml").read_text()
    captured = capsys.readouterr()
    assert captured.out == expected_output


def test_output_dir(tmp_path, fixtures_dir, default_config_file, execute_jenkins_jobs):
    """
    Run test mode with output to directory and verify that output files are
    generated.
    """
    args = ["test", str(fixtures_dir / "cmd-001.yaml"), "-o", str(tmp_path)]
    execute_jenkins_jobs(args)
    assert tmp_path.joinpath("foo-job").exists()


def test_output_dir_config_xml(tmp_path, fixtures_dir, execute_jenkins_jobs):
    """
    Run test mode with output to directory in "config.xml" mode and verify
    that output files are generated.
    """
    args = [
        "test",
        str(fixtures_dir / "cmd-001.yaml"),
        "-o",
        str(tmp_path),
        "--config-xml",
    ]
    execute_jenkins_jobs(args)
    assert tmp_path.joinpath("foo-job", "config.xml").exists()


def test_stream_input_output_no_encoding_exceed_recursion(
    mocker, fixtures_dir, execute_jenkins_jobs
):
    """
    Test that we don't have issues processing large number of jobs and
    outputting the result if the encoding is not set.
    """
    console_out = io.BytesIO()
    console_out.encoding = None
    mocker.patch("sys.stdout", console_out)

    input = fixtures_dir.joinpath("large-number-of-jobs-001.yaml").read_bytes()
    mocker.patch("sys.stdin", io.BytesIO(input))

    args = ["test"]
    execute_jenkins_jobs(args)


def test_stream_input_output_utf8_encoding(
    capsys, mocker, fixtures_dir, default_config_file, execute_jenkins_jobs
):
    """
    Run test mode simulating using pipes for input and output using
    utf-8 encoding
    """
    input = fixtures_dir.joinpath("cmd-001.yaml").read_bytes()
    mocker.patch("sys.stdin", io.BytesIO(input))

    args = ["--conf", default_config_file, "test"]
    execute_jenkins_jobs(args)

    expected_output = fixtures_dir.joinpath("cmd-001.xml").read_text()
    captured = capsys.readouterr()
    assert captured.out == expected_output


def test_stream_input_output_ascii_encoding(
    mocker, fixtures_dir, default_config_file, execute_jenkins_jobs
):
    """
    Run test mode simulating using pipes for input and output using
    ascii encoding with unicode input
    """
    console_out = io.BytesIO()
    console_out.encoding = "ascii"
    mocker.patch("sys.stdout", console_out)

    input = fixtures_dir.joinpath("cmd-001.yaml").read_bytes()
    mocker.patch("sys.stdin", io.BytesIO(input))

    args = ["--conf", default_config_file, "test"]
    execute_jenkins_jobs(args)

    expected_output = fixtures_dir.joinpath("cmd-001.xml").read_text()
    output = console_out.getvalue().decode("ascii")
    assert output == expected_output


def test_stream_output_ascii_encoding_invalid_char(
    mocker, fixtures_dir, default_config_file
):
    """
    Run test mode simulating using pipes for input and output using
    ascii encoding for output with include containing a character
    that cannot be converted.
    """
    console_out = io.BytesIO()
    console_out.encoding = "ascii"
    mocker.patch("sys.stdout", console_out)

    input = fixtures_dir.joinpath("unicode001.yaml").read_bytes()
    mocker.patch("sys.stdin", io.BytesIO(input))

    args = ["--conf", default_config_file, "test"]
    jenkins_jobs = entry.JenkinsJobs(args)
    with pytest.raises(UnicodeError) as excinfo:
        jenkins_jobs.execute()
    assert "'ascii' codec can't encode character" in str(excinfo.value)


def test_plugins_info_stub_option(mocker, fixtures_dir, execute_jenkins_jobs):
    """
    Test handling of plugins_info stub option.
    """
    mocker.patch("jenkins_jobs.cli.subcommand.base.XmlJobGenerator.generateXML")
    registry_mock = mocker.patch("jenkins_jobs.cli.subcommand.base.ModuleRegistry")

    plugins_info_stub_yaml_file = fixtures_dir / "plugins-info.yaml"
    args = [
        "--conf",
        str(fixtures_dir / "cmd-001.conf"),
        "test",
        "-p",
        str(plugins_info_stub_yaml_file),
        str(fixtures_dir / "cmd-001.yaml"),
    ]

    execute_jenkins_jobs(args)

    plugins_info_list = yaml.safe_load(plugins_info_stub_yaml_file.read_text())

    registry_mock.assert_called_with(mock.ANY, plugins_info_list)


def test_bogus_plugins_info_stub_option(
    capsys, mocker, fixtures_dir, default_config_file
):
    """
    Verify that a JenkinsJobException is raised if the plugins_info stub
    file does not yield a list as its top-level object.
    """
    mocker.patch("jenkins_jobs.cli.subcommand.base.XmlJobGenerator.generateXML")
    mocker.patch("jenkins_jobs.cli.subcommand.base.ModuleRegistry")

    plugins_info_stub_yaml_file = fixtures_dir / "bogus-plugins-info.yaml"
    args = [
        "--conf",
        str(fixtures_dir / "cmd-001.conf"),
        "test",
        "-p",
        str(plugins_info_stub_yaml_file),
        str(fixtures_dir / "cmd-001.yaml"),
    ]

    with pytest.raises(SystemExit):
        entry.JenkinsJobs(args)

    captured = capsys.readouterr()
    assert "must contain a Yaml list" in captured.err


# Test without mocking get_plugins_info.
#
# This test class is used for testing the 'test' subcommand when we want
# to validate its behavior without mocking
# jenkins_jobs.builder.JenkinsManager.get_plugins_info


def test_console_output_jenkins_connection_failure_warning(
    caplog, mocker, fixtures_dir, execute_jenkins_jobs
):
    """
    Run test mode and verify that failed Jenkins connection attempt
    exception does not bubble out of cmd.main.
    """
    mocker.patch(
        "jenkins.Jenkins.get_plugins",
        side_effect=jenkins.JenkinsException("Connection refused"),
    )

    try:
        args = [
            "--conf",
            str(fixtures_dir / "enable-query-plugins.conf"),
            "test",
            str(fixtures_dir / "cmd-001.yaml"),
        ]
        execute_jenkins_jobs(args)
    except jenkins.JenkinsException:
        pytest.fail("jenkins.JenkinsException propagated to main")
    except Exception:
        pass  # only care about jenkins.JenkinsException for now
    assert "Unable to retrieve Jenkins Plugin Info" in caplog.text


def test_skip_plugin_retrieval_if_no_config_provided(
    mocker, fixtures_dir, default_config_file
):
    """
    Verify that retrieval of information from Jenkins instance about its
    plugins will be skipped when run if no config file provided.
    """
    get_plugins_mock = mocker.patch("jenkins.Jenkins.get_plugins")
    args = [
        "--conf",
        default_config_file,
        "test",
        str(fixtures_dir / "cmd-001.yaml"),
    ]
    entry.JenkinsJobs(args)
    assert not get_plugins_mock.called


@mock.patch("jenkins.Jenkins.get_plugins_info")
def test_skip_plugin_retrieval_if_disabled(mocker, fixtures_dir):
    """
    Verify that retrieval of information from Jenkins instance about its
    plugins will be skipped when run if a config file provided and disables
    querying through a config option.
    """
    get_plugins_mock = mocker.patch("jenkins.Jenkins.get_plugins")
    args = [
        "--conf",
        str(fixtures_dir / "disable-query-plugins.conf"),
        "test",
        str(fixtures_dir / "cmd-001.yaml"),
    ]
    entry.JenkinsJobs(args)
    assert not get_plugins_mock.called


class MatchesDirMissingFilesMismatch(object):
    def __init__(self, left_directory, right_directory):
        self.left_directory = left_directory
        self.right_directory = right_directory

    def describe(self):
        return "{0} and {1} contain different files".format(
            self.left_directory, self.right_directory
        )

    def get_details(self):
        return {}


class MatchesDirFileContentsMismatch(object):
    def __init__(self, left_file, right_file):
        self.left_file = left_file
        self.right_file = right_file

    def describe(self):
        left_contents = open(self.left_file).readlines()
        right_contents = open(self.right_file).readlines()

        return "{0} is not equal to {1}:\n{2}".format(
            difflib.unified_diff(
                left_contents,
                right_contents,
                fromfile=self.left_file,
                tofile=self.right_file,
            ),
            self.left_file,
            self.right_file,
        )

    def get_details(self):
        return {}


class MatchesDir(object):
    def __init__(self, directory):
        self.__directory = directory
        self.__files = self.__get_files(directory)

    def __get_files(self, directory):
        for root, _, files in os.walk(directory):
            return files

    def __str__(self, directory):
        return "MatchesDir({0})".format(self.__dirname)

    def match(self, other_directory):
        other_files = self.__get_files(other_directory)

        self.__files.sort()
        other_files.sort()

        if self.__files != other_files:
            return MatchesDirMissingFilesMismatch(self.__directory, other_directory)

        for i, file in enumerate(self.__files):
            my_file = os.path.join(self.__directory, file)
            other_file = os.path.join(other_directory, other_files[i])
            if not filecmp.cmp(my_file, other_file):
                return MatchesDirFileContentsMismatch(my_file, other_file)

        return None


@pytest.fixture
def multipath(fixtures_dir):
    path_list = [
        str(fixtures_dir / "multi-path/yamldirs/" / p) for p in ["dir1", "dir2"]
    ]
    return os.pathsep.join(path_list)


@pytest.fixture
def output_dir(tmp_path):
    dir = tmp_path / "output"
    dir.mkdir()
    return str(dir)


def test_multi_path(
    fixtures_dir, default_config_file, execute_jenkins_jobs, output_dir, multipath
):
    """
    Run test mode and pass multiple paths.
    """
    args = [
        "--conf",
        default_config_file,
        "test",
        "-o",
        output_dir,
        multipath,
    ]

    execute_jenkins_jobs(args)
    assert_that(output_dir, MatchesDir(fixtures_dir / "multi-path/output_simple"))


def test_recursive_multi_path_command_line(
    fixtures_dir, default_config_file, execute_jenkins_jobs, output_dir, multipath
):
    """
    Run test mode and pass multiple paths with recursive path option.
    """
    args = [
        "--conf",
        default_config_file,
        "test",
        "-o",
        output_dir,
        "-r",
        multipath,
    ]

    execute_jenkins_jobs(args)
    assert_that(output_dir, MatchesDir(fixtures_dir / "multi-path/output_recursive"))


def test_recursive_multi_path_config_file(
    fixtures_dir, execute_jenkins_jobs, output_dir, multipath
):
    # test recursive set in configuration file
    args = [
        "--conf",
        str(fixtures_dir / "multi-path/builder-recursive.ini"),
        "test",
        "-o",
        output_dir,
        multipath,
    ]
    execute_jenkins_jobs(args)
    assert_that(output_dir, MatchesDir(fixtures_dir / "multi-path/output_recursive"))


def test_recursive_multi_path_with_excludes(
    fixtures_dir, default_config_file, execute_jenkins_jobs, output_dir, multipath
):
    """
    Run test mode and pass multiple paths with recursive path option.
    """
    exclude_path = fixtures_dir / "multi-path/yamldirs/dir2/dir1"
    args = [
        "--conf",
        default_config_file,
        "test",
        "-x",
        str(exclude_path),
        "-o",
        output_dir,
        "-r",
        multipath,
    ]

    execute_jenkins_jobs(args)
    assert_that(
        output_dir,
        MatchesDir(fixtures_dir / "multi-path/output_recursive_with_excludes"),
    )
