# Copyright 2013 Hewlett-Packard Development Company, L.P.
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


"""
The MultiJob Project module handles creating MultiJob Jenkins projects.
You may specify ``multijob`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Tye MultiJob plugin is required.

Example::

  job:
    name: test_job
    project-type: multijob
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class MultiJob(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('com.tikal.jenkins.plugins.multijob.'
                                 'MultiJobProject')
        return xml_parent
