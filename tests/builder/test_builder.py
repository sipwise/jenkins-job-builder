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

import os
import shutil
import tempfile

import jenkins_jobs.builder
from tests.base import mock
from testtools import TestCase


@mock.patch('jenkins_jobs.builder.CacheStorage', mock.MagicMock)
class BuilderPluginListTests(TestCase):
    def setUp(self):
        self.builder = jenkins_jobs.builder.Builder(
            'http://jenkins.example.com',
            'doesnot', 'matter',
            plugins_list=['plugin1', 'plugin2'],
        )
        TestCase.setUp(self)

    def test_plugins_list(self):
        self.assertEqual(self.builder.plugins_list, ['plugin1', 'plugin2'])

    @mock.patch.object(jenkins_jobs.builder.jenkins.Jenkins,
                       'get_plugins_info', return_value=['p1', 'p2'])
    def test_plugins_list_from_jenkins(self, jenkins_mock):
        # Trigger fetching the plugins from jenkins when accessing the property
        self.builder._plugins_list = None
        self.assertEqual(self.builder.plugins_list, ['p1', 'p2'])


@mock.patch('jenkins_jobs.builder.CacheStorage', mock.MagicMock)
class BuilderUpdateJobTests(TestCase):
    def setUp(self):
        self.yaml_fn = os.path.join(os.path.dirname(__file__), 'job.yaml')
        self.xml_fn = os.path.join(os.path.dirname(__file__), 'job.xml')
        self.builder = jenkins_jobs.builder.Builder(
            'http://jenkins.example.com',
            'doesnot', 'matter',
            plugins_list=[],
        )
        TestCase.setUp(self)

    def check_xml(self, outfp):
        with open(self.xml_fn) as fp:
            expected = fp.read()

        xml = outfp.read()
        self.assertEqual(xml, expected)

    def test_update_job_open_file(self):
        with tempfile.NamedTemporaryFile(mode='w+') as tmpfile:
            jobs, updated_jobs = self.builder.update_job([self.yaml_fn],
                                                         output=tmpfile)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].name, 'foo-job')
            self.assertEqual(updated_jobs, 0)

            tmpfile.seek(0)
            self.check_xml(tmpfile)

    def test_update_job_directory(self):
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)

        jobs, updated_jobs = self.builder.update_job([self.yaml_fn],
                                                     output=tmpdir)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].name, 'foo-job')
        self.assertEqual(updated_jobs, 0)

        outfn = os.path.join(tmpdir, 'foo-job')
        with open(outfn) as outfp:
            self.check_xml(outfp)
