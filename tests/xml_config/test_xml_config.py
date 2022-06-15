# Copyright 2016 Hewlett Packard Enterprise
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

from pathlib import Path

import pytest

from jenkins_jobs.config import JJBConfig
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.registry import ModuleRegistry
from jenkins_jobs.xml_config import XmlJobGenerator, XmlViewGenerator


fixtures_dir = Path(__file__).parent / "exceptions"


@pytest.fixture
def config():
    config = JJBConfig()
    config.validate()
    return config


@pytest.fixture
def parser(config):
    return YamlParser(config)


@pytest.fixture
def registry(config):
    return ModuleRegistry(config)


def test_invalid_project(parser, registry):
    parser.parse(str(fixtures_dir / "invalid_project.yaml"))
    jobs, views = parser.expandYaml(registry)

    generator = XmlJobGenerator(registry)

    with pytest.raises(JenkinsJobsException) as excinfo:
        generator.generateXML(jobs)
    assert "Unrecognized project-type:" in str(excinfo.value)


def test_invalid_view(parser, registry):
    parser.parse(str(fixtures_dir / "invalid_view.yaml"))
    jobs, views = parser.expandYaml(registry)

    generator = XmlViewGenerator(registry)

    with pytest.raises(JenkinsJobsException) as excinfo:
        generator.generateXML(views)
    assert "Unrecognized view-type:" in str(excinfo.value)


def test_template_params(caplog, parser, registry):
    parser.parse(str(fixtures_dir / "failure_formatting_component.yaml"))
    registry.set_parser_data(parser.data)
    jobs, views = parser.expandYaml(registry)

    generator = XmlJobGenerator(registry)

    with pytest.raises(Exception):
        generator.generateXML(jobs)
    assert "Failure formatting component" in caplog.text
    assert "Problem formatting with args" in caplog.text
