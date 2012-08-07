# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from setuptools import find_packages
from setuptools import setup

setup(name='jenkins_job_builder',
      version='0.1',
      description="Manage Jenkins jobs with YAML",
      license='Apache License (2.0)',
      author='Hewlett-Packard Development Company, L.P.',
      author_email='openstack@lists.launchpad.net',
      scripts=['jenkins-jobs'],
      include_package_data=True,
      zip_safe=False,
      packages=find_packages(),

      entry_points = {
        'jenkins_jobs.modules': [
            'freestyle=jenkins_jobs.modules.project_freestyle:Freestyle',
            'maven=jenkins_jobs.modules.project_maven:Maven',

            'assignednode=jenkins_jobs.modules.assignednode:AssignedNode',
            'builders=jenkins_jobs.modules.builders:Builders',
            'logrotate=jenkins_jobs.modules.logrotate:LogRotate',
            'properties=jenkins_jobs.modules.properties:Properties',
            'publishers=jenkins_jobs.modules.publishers:Publishers',
            'scm=jenkins_jobs.modules.scm:SCM',
            'triggers=jenkins_jobs.modules.triggers:Triggers',
            'wrappers=jenkins_jobs.modules.wrappers:Wrappers',
            'zuul=jenkins_jobs.modules.zuul:Zuul',
            ]
        }

      )
