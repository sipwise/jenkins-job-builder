# -*- coding: utf-8 -*-
# Copyright (C) 2015 David Caro <david@dcaro.es>
#
# Based on jenkins_jobs/modules/project_flow.py by
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
The workflow Project module handles creating Jenkins workflow projects.
You may specify ``workflow`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Requires the Jenkins :jenkins-wiki:`Workflow Plugin <Workflow+Plugin>` or the
:jenkins-wiki:`Pipeline Plugin <Pipeline+Plugin>`:

* with the former (Workflow Plugin), you must write the flow steps in DSL
  within the job's configuration
* with the later (Pipeline Plugin) you can benefit from the new Jenkins
  "`Pipeline as code`_" feature. In other words you can configure your job
  inside a Groovy file lying with the source code.

In order to write an inline script within a job-template you have to escape the
curly braces by doubling them in the DSL: { -> {{ , otherwise it will be
interpreted by the python str.format() command.

:Job Parameters:
    * **sandbox** (`bool`): If the script should run in a sandbox (default
      false)
    * **dsl** (`str`): The DSL content or,
    * **workflow-scm** (`str`): in case "Pipeline as code" feature is used.
      Then you should specify:

        * **scm**: reference to an ``scm`` component describing the source code
          repository
        * **script-name**: name of the Groovy file containing the job's steps
          (optional, default: ``Jenkinsfile``)

Note that ``dsl`` and ``workflow-scm`` parameters are mutually exclusive.

Inline DSL job example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_workflow_template001.yaml

Inline DSL job template example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_workflow_template002.yaml

"Pipeline as code" example:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_workflow_template004.yaml

"Pipeline as code" example using templates:

    .. literalinclude::
      /../../tests/yamlparser/fixtures/project_workflow_template005.yaml

.. _Pipeline as code: https://jenkins.io/solutions/pipeline/

"""
import xml.etree.ElementTree as XML

from jenkins_jobs.errors import JenkinsJobsException
import jenkins_jobs.modules.base


class Workflow(jenkins_jobs.modules.base.Base):
    sequence = 0
    error_msg = ("You cannot declare both 'dsl' and 'workflow-scm' on a "
                 "workflow job")

    def root_xml(self, data):
        xml_parent = XML.Element('flow-definition',
                                 {'plugin': 'workflow-job'})
        if 'dsl' in data and 'workflow-scm' in data:
            raise JenkinsJobsException(self.error_msg)
        if 'dsl' in data:
            xml_definition = XML.SubElement(xml_parent, 'definition',
                                            {'plugin': 'workflow-cps',
                                             'class': 'org.jenkinsci.plugins.'
                                             'workflow.cps.CpsFlowDefinition'})
            XML.SubElement(xml_definition, 'script').text = data['dsl']
        else:
            xml_definition = XML.SubElement(xml_parent, 'definition', {
                'plugin': 'workflow-cps',
                'class': 'org.jenkinsci.plugins.workflow.cps.'
                'CpsScmFlowDefinition'})

        needs_workspace = data.get('sandbox', False)
        XML.SubElement(xml_definition, 'sandbox').text = str(
            needs_workspace).lower()

        return xml_parent
