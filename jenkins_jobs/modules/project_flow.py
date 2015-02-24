# -*- coding: utf-8 -*-
# Copyright (C) 2013 eNovance SAS <licensing@enovance.com>
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
The flow Project module handles creating Jenkins flow projects.
You may specify ``flow`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Requires the Jenkins `Build Flow Plugin.
<https://wiki.jenkins-ci.org/display/JENKINS/Build+Flow+Plugin>`_

In order to use it for job-template you have to escape the curly braces by
doubling them in the DSL: { -> {{ , otherwise it will be interpreted by the
python str.format() command.

:arg str dsl: The sequence of jobs to be built.
:arg bool build-needs-workspace: This build needs a workspace (default: False)

Job example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_flow_template001.yaml

Job template example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_flow_template002.yaml

"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class Flow(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element('com.cloudbees.plugins.flow.BuildFlow')
        if 'dsl' in data:
            XML.SubElement(xml_parent, 'dsl').text = data['dsl']
        else:
            XML.SubElement(xml_parent, 'dsl').text = ''

        if 'build-needs-workspace' in data:
            XML.SubElement(xml_parent, 'buildNeedsWorkspace').text = str(
                data.get('build-needs-workspace', False)).lower()

        return xml_parent
