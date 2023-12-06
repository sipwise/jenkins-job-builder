#!/usr/bin/env python
#
# Copyright 2013 Darragh Bailey
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

from io import StringIO
from pathlib import Path
from yaml import safe_dump

import json
import pytest
from yaml.composer import ComposerError

from jenkins_jobs.config import JJBConfig

from jenkins_jobs.roots import Roots
from jenkins_jobs.loader import Loader, load_files
from jenkins_jobs.registry import ModuleRegistry
from tests.enum_scenarios import scenario_list


fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture
def read_input(scenario, jjb_config):
    def read():
        loader = Loader(
            scenario.in_path.read_text(),
            jjb_config=jjb_config,
            source_path=scenario.in_path,
            source_dir=scenario.in_path.parent,
        )
        return loader.get_single_data()

    return read


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(s, id=s.name)
        for s in scenario_list(fixtures_dir, out_ext=".json")
        if not s.name.startswith(("custom_", "exception_"))
    ],
)
def test_include(scenario, jjb_config, expected_output):
    """
    Verify application specific tags independently of any changes to
    modules XML parsing behaviour
    """

    roots = Roots(jjb_config)
    load_files(jjb_config, roots, [scenario.in_path])
    job_data_list = [dict(sorted(j.data.items())) for j in roots.generate_jobs()]
    pretty_json = json.dumps(job_data_list, indent=4)
    print(pretty_json)
    assert pretty_json == expected_output.strip()


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(s, id=s.name)
        for s in scenario_list(fixtures_dir)
        if not s.name.startswith(("custom_", "exception_")) and s.out_paths
    ],
)
def test_include_job(check_job):
    check_job()


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(s, id=s.name)
        for s in scenario_list(fixtures_dir, out_ext=".json")
        if s.name.startswith("exception_")
    ],
)
def test_include_error(check_job):
    with pytest.raises(ComposerError) as excinfo:
        check_job()
    assert str(excinfo.value).startswith("found duplicate anchor ")


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(s, id=s.name)
        for s in scenario_list(fixtures_dir, in_ext=".iyaml", out_ext=".oyaml")
    ],
)
def test_anchor_alias(read_input, expected_output):
    """
    Verify yaml input is expanded to the expected yaml output when using yaml
    anchors and aliases.
    """

    input = read_input()
    data = StringIO(json.dumps(input))
    pretty_yaml = safe_dump(json.load(data), default_flow_style=False)
    assert expected_output == pretty_yaml


def test_include_anchors():
    """
    Verify that anchors/aliases only span use of '!include' tag

    To ensure that any yaml loaded by the include tag is in the same
    space as the top level file, but individual top level yaml definitions
    are treated by the yaml loader as independent.
    """

    config = JJBConfig()
    config.jenkins["url"] = "http://example.com"
    config.jenkins["user"] = "jenkins"
    config.jenkins["password"] = "password"
    config.builder["plugins_info"] = []
    config.validate()

    files = [
        "custom_same_anchor-001-part1.yaml",
        "custom_same_anchor-001-part2.yaml",
    ]

    roots = Roots(config)
    # Should not raise ComposerError.
    load_files(config, roots, [fixtures_dir / name for name in files])


def test_retain_anchor_default():
    """
    Verify that anchors are NOT retained across files by default.
    """

    config = JJBConfig()
    config.validate()

    files = [
        "custom_retain_anchors_include001.yaml",
        "custom_retain_anchors.yaml",
    ]

    roots = Roots(config)
    with pytest.raises(ComposerError) as excinfo:
        load_files(config, roots, [fixtures_dir / name for name in files])
    assert "found undefined alias" in str(excinfo.value)


def test_retain_anchors_enabled():
    """
    Verify that anchors are retained across files if retain_anchors is
    enabled in the config.
    """

    config = JJBConfig()
    config.yamlparser["retain_anchors"] = True
    config.validate()

    files = [
        "custom_retain_anchors_include001.yaml",
        "custom_retain_anchors.yaml",
    ]

    roots = Roots(config)
    # Should not raise ComposerError.
    load_files(config, roots, [fixtures_dir / name for name in files])


def test_retain_anchors_enabled_j2_yaml():
    """
    Verify that anchors are retained across files and are properly retained when using !j2-yaml.
    """

    config = JJBConfig()
    config.yamlparser["retain_anchors"] = True
    config.validate()

    files = [
        "custom_retain_anchors_j2_yaml_include001.yaml",
        "custom_retain_anchors_j2_yaml.yaml",
    ]

    roots = Roots(config)
    load_files(config, roots, [fixtures_dir / name for name in files])

    registry = ModuleRegistry(config, None)
    registry.set_macros(roots.macros)
    jobs = roots.generate_jobs()
    assert "docker run ubuntu:latest" == jobs[0].data["builders"][0]["shell"]
