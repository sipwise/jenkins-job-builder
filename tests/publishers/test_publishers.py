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
from jenkins_jobs.modules import publishers
from tests import base

# This dance deals with the fact that we want unittest.mock if
# we're on Python 3.4 and later, and non-stdlib mock otherwise.
try:
    from unittest import mock
except ImportError:
    import mock  # noqa


class TestCaseModulePublishers(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = base.get_scenarios(fixtures_path)
    klass = publishers.Publishers


class TestKeepBuildForever(base.BaseTestCase):

    def test_keep_build_forever_not_allowed_unless_in_publish_steps(self):
        registry = mock.MagicMock()
        xml_parent = XML.Element('publishers')
        data = 'dont_care'

        self.assertRaises(JenkinsJobsException, publishers.keep_build_forever,
                          registry, xml_parent, data)
