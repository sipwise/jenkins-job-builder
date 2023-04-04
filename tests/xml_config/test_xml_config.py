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
from jenkins_jobs.xml_config import XmlJobGenerator, XmlViewGenerator
from jenkins_jobs.roots import Roots
from jenkins_jobs.loader import load_files


fixtures_dir = Path(__file__).parent / "exceptions"


# Override jjb_config and plugins_info so that scenarios won't be used.
@pytest.fixture
def jjb_config():
    config = JJBConfig()
    config.validate()
    return config


@pytest.fixture
def plugins_info():
    return None


@pytest.fixture
def parser(jjb_config, registry):
    def parse(fname):
        roots = Roots(jjb_config)
        load_files(jjb_config, roots, [fixtures_dir / fname])
        registry.set_macros(roots.macros)
        return roots

    return parse


def test_invalid_project(parser, registry):
    roots = parser("invalid_project.yaml")
    jobs = roots.generate_jobs()
    generator = XmlJobGenerator(registry)

    with pytest.raises(JenkinsJobsException) as excinfo:
        generator.generateXML(jobs)
    assert "Unrecognized project-type:" in str(excinfo.value)


def test_invalid_view(parser, registry):
    roots = parser("invalid_view.yaml")
    views = roots.generate_views()
    generator = XmlViewGenerator(registry)

    with pytest.raises(JenkinsJobsException) as excinfo:
        generator.generateXML(views)
    assert "Unrecognized view-type:" in str(excinfo.value)


def test_template_params(parser, registry):
    roots = parser("failure_formatting_component.yaml")
    jobs = roots.generate_jobs()
    generator = XmlJobGenerator(registry)

    with pytest.raises(Exception) as excinfo:
        generator.generateXML(jobs)
    message = "While formatting string '{branches}': Missing parameter: 'branches'"
    assert str(excinfo.value) == message


def test_missing_j2_param(parser, registry):
    roots = parser("missing_j2_parameter.yaml")
    jobs = roots.generate_jobs()
    generator = XmlJobGenerator(registry)

    with pytest.raises(Exception) as excinfo:
        generator.generateXML(jobs)
    message = "'branches' is undefined"
    assert str(excinfo.value) == message


def test_missing_include_j2_param(parser, registry):
    roots = parser("missing_include_j2_parameter.yaml")
    jobs = roots.generate_jobs()
    generator = XmlJobGenerator(registry)

    with pytest.raises(Exception) as excinfo:
        generator.generateXML(jobs)
    message = "'branches' is undefined"
    assert str(excinfo.value) == message
