# vim: set fileencoding=utf-8 :
#
#  - Copyright 2014 Guido Günther <agx@sigxcpu.org>
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

import mock

from jenkins import JenkinsException
import jenkins_jobs.builder

from testtools import TestCase


class TestCaseTestBuilder(TestCase):
    def setUp(self):
        self.builder = jenkins_jobs.builder.Builder(
            'http://jenkins.example.com',
            'doesnot', 'matter',
            jenkins_timeout=1,
            plugins_list=['plugin1', 'plugin2'],
        )
        TestCase.setUp(self)

    @mock.patch.object(jenkins_jobs.builder.Jenkins, 'get_info',
                       return_value={'mode': 'NORMAL'})
    def test_wait_for_ready_jenkins(self, jenkins_mock):
        "Wait for a jenkins that is already working fine"
        self.assertEqual(self.builder.jenkins.get_info()['mode'], "NORMAL")

    @mock.patch.object(jenkins_jobs.builder.Jenkins, 'get_info',
                       return_value={})
    def test_wait_for_jenkins_timeout(self, jenkins_mock):
        "Wait for a jenkins that doesn't start up in time but outputs JSON"
        self.assertEqual(self.builder.wait_for_jenkins(1), False)

    @mock.patch.object(jenkins_jobs.builder.Jenkins, 'get_info',
                       side_effect=JenkinsException('Foo Connection refused'))
    def test_wait_for_jenkins_conn_refused(self, jenkins_mock):
        "Bail out of a jenkins with a permanent error"
        self.assertEqual(self.builder.wait_for_jenkins(1), False)

    @mock.patch.object(jenkins_jobs.builder.Jenkins, 'get_info',
                       side_effect=JenkinsException('other error'))
    def test_wait_for_jenkins_failure(self, jenkins_mock):
        "Bail out of a jenkins with a permanent error"
        self.assertRaises(JenkinsException, self.builder.wait_for_jenkins, 1)

    def test_plugins_list(self):
        self.assertEqual(self.builder.plugins_list, ['plugin1', 'plugin2'])

    @mock.patch.object(jenkins_jobs.builder.Jenkins, 'get_plugins_info',
                       return_value=['p1', 'p2'])
    def test_plugins_list_from_jenkins(self, jenkins_mock):
        # Trigger fetching the plugins from jenkins when accessing the property
        self.builder._plugins_list = None
        self.assertEqual(self.builder.plugins_list, ['p1', 'p2'])
