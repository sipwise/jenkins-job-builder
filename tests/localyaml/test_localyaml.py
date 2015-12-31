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

import os
from testtools import ExpectedException
from testtools import TestCase
from testscenarios.testcase import TestWithScenarios
from yaml.composer import ComposerError

from jenkins_jobs.config import JJBConfig
from jenkins_jobs.parser import YamlParser
from tests.base import get_scenarios, JsonTestCase, YamlTestCase
from tests.base import LoggingFixture


def _exclude_scenarios(input_filename):
    return os.path.basename(input_filename).startswith("custom_")


class TestCaseLocalYamlInclude(TestWithScenarios, JsonTestCase, TestCase):
    """
    Verify application specific tags independently of any changes to
    modules XML parsing behaviour
    """
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path, 'yaml', 'json',
                              filter_func=_exclude_scenarios)

    def test_yaml_snippet(self):

        if os.path.basename(self.in_filename).startswith("exception_"):
            with ExpectedException(ComposerError,
                                   "^found duplicate anchor .*"):
                super(TestCaseLocalYamlInclude, self).test_yaml_snippet()
        else:
            super(TestCaseLocalYamlInclude, self).test_yaml_snippet()


class TestCaseLocalYamlAnchorAlias(TestWithScenarios, YamlTestCase, TestCase):
    """
    Verify yaml input is expanded to the expected yaml output when using yaml
    anchors and aliases.
    """
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path, 'iyaml', 'oyaml')


class TestCaseLocalYamlIncludeAnchors(LoggingFixture, TestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')

    def test_multiple_same_anchor_in_multiple_toplevel_yaml(self):
        """
        Verify that anchors/aliases only span use of '!include' tag

        To ensure that any yaml loaded by the include tag is in the same
        space as the top level file, but individual top level yaml definitions
        are treated by the yaml loader as independent.
        """

        files = ["custom_same_anchor-001-part1.yaml",
                 "custom_same_anchor-001-part2.yaml"]

        jjb_config = JJBConfig()
        jjb_config.do_magical_things()
        jjb_config.jenkins['url'] = 'http://example.com'
        jjb_config.jenkins['user'] = 'jenkins'
        jjb_config.jenkins['password'] = None
        jjb_config.builder['plugins_list'] = []
        j = YamlParser(jjb_config)
        j.load_files([os.path.join(self.fixtures_path, f) for f in files])
