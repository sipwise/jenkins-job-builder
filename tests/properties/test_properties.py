# Joint copyright:
#  - Copyright 2012,2013 Wikimedia Foundation
#  - Copyright 2012,2013 Antoine "hashar" Musso
#  - Copyright 2013 Arnaud Fabre
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
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.modules import properties
from tests import base

# This dance deals with the fact that we want unittest.mock if
# we're on Python 3.4 and later, and non-stdlib mock otherwise.
try:
    from unittest import mock
except ImportError:
    import mock  # noqa


class TestCaseModuleProperties(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = base.get_scenarios(fixtures_path)
    klass = properties.Properties


class TestPromotedBuild(base.BaseTestCase):

    def test_data_manipulation_and_callback(self):
        registry = mock.MagicMock()
        registry.module_callbacks = {'add_promoted_build': mock.MagicMock()}
        xml_parent = XML.Element('i_dont_care')
        data1_before = {'name': 'stage'}
        data1_after = {'name': 'stage',
                       'build-steps': [],
                       'publish-steps': [],
                       'project-type': 'promoted_builds'}
        data2_before = {'name': 'prod',
                        'build-steps': ['leave_me_be'],
                        'publish-steps': ['leave_me_be']}
        data2_after = {'name': 'prod',
                       'build-steps': ['leave_me_be'],
                       'publish-steps': ['leave_me_be'],
                       'project-type': 'promoted_builds'}
        data = [data1_before, data2_before]

        properties.promoted_build(registry, xml_parent, data)

        registry.module_callbacks['add_promoted_build'].assert_has_calls(
            [mock.call(data1_after), mock.call(data2_after)])

    def test_recursive_promotions_not_allowed(self):
        registry = mock.MagicMock()
        xml_parent = XML.Element('i_dont_care')
        data = [
            {
                'name': 'invalid promotion',
                'properties': [
                    {
                        'promoted-build': {
                            'name': 'promoted-build is not valid here'
                        }
                    }
                ]
            }
        ]

        self.assertRaises(JenkinsJobsException, properties.promoted_build,
                          registry, xml_parent, data)
