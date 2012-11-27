# Copyright 2012 Hewlett-Packard Development Company, L.P.
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
The JDK section allows you to specify which Jenkins JDK
should run the specified job.  It adds the ``jdk``
attribute to the :ref:`Job` definition.

Example::

  job:
    name: test_job
    java: java6

That speficies that the job should be run on a Jenkins JDK
named ``java6``.
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class JDK(jenkins_jobs.modules.base.Base):
    sequence = 40

    def gen_xml(self, parser, xml_parent, data):
        node = data.get('jdk', None)
        if node:
            XML.SubElement(xml_parent, 'jdk').text = node
