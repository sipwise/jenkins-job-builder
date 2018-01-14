# Joint copyright:
#  - Copyright 2014 Hewlett-Packard Development Company, L.P.
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
import mock

from testtools import ExpectedException

from jenkins_jobs.errors import JenkinsJobsException
from tests import base
from tests.base import mock

# os.path.isfile is mocked to prevent usage of config files that may
# be existing on the test machine.
original_isfile = os.path.isfile

class TestCaseModuleDuplicates(base.SingleJobTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = base.get_scenarios(fixtures_path)

    def isfile_sideeffect(*args, **kwargs):

        if args[0] in [
            '/etc/jenkins_jobs/jenkins_jobs.ini',
            os.path.join(os.path.expanduser('~'), '.config', 'jenkins_jobs', 'jenkins_jobs.ini'),
            os.path.join(os.path.dirname(__file__), 'jenkins_jobs.ini')]:
                return False

        return original_isfile(args[0])

    @mock.patch('jenkins_jobs.builder.logger', autospec=True)
    @mock.patch('os.path.isfile', side_effect = isfile_sideeffect)
    def test_yaml_snippet(self, mock_logger, mock_isfile):

        if os.path.basename(self.in_filename).startswith("exception_"):
            with ExpectedException(JenkinsJobsException, "^Duplicate .*"):
                super(TestCaseModuleDuplicates, self).test_yaml_snippet()
        else:
            super(TestCaseModuleDuplicates, self).test_yaml_snippet()
