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
The Properties module supplies a wide range of options that are
implemented as Jenkins job properties, from the obvious (job
parameters) to the less obvious (job throttling).

The module defines three kinds of components, all of which accept
lists of components in the :ref:`Job` definition.  They may be
components defined below, locally defined macros, or locally defined
components found via entry points.

**Component**: properties
  :Macro: property
  :Entry Point: jenkins_jobs.properties

**Component**: parameters
  :Macro: parameter
  :Entry Point: jenkins_jobs.parameters

**Component**: notifications
  :Macro: notification
  :Entry Point: jenkins_jobs.notifications

Example::

  job:
    name: test_job

    properties:
      - github:
          url: https://github.com/openstack-ci/jenkins-job-builder/

    parameters:
      - string:
          name: FOO
          default: bar
          description: "A parameter named FOO, defaults to 'bar'."

    notifications:
      - http:
          url: http://example.com/jenkins_endpoint
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def base_param(parser, xml_parent, data, do_default, ptype):
    pdef = XML.SubElement(xml_parent, ptype)
    XML.SubElement(pdef, 'name').text = data['name']
    XML.SubElement(pdef, 'description').text = data['description']
    if do_default:
        default = data.get('default', None)
        if default:
            XML.SubElement(pdef, 'defaultValue').text = default
        else:
            XML.SubElement(pdef, 'defaultValue')


def string_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
               'hudson.model.StringParameterDefinition')


def bool_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
               'hudson.model.BooleanParameterDefinition')


def file_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, False,
               'hudson.model.FileParameterDefinition')


def text_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
               'hudson.model.TextParameterDefinition')


def label_param(parser, xml_parent, data):
    base_param(parser, xml_parent, data, True,
      'org.jvnet.jenkins.plugins.nodelabelparameter.LabelParameterDefinition')


class Parameters(jenkins_jobs.modules.base.Base):
    sequence = 21

    def gen_xml(self, parser, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        parameters = data.get('parameters', [])
        if parameters:
            pdefp = XML.SubElement(properties,
                                   'hudson.model.ParametersDefinitionProperty')
            pdefs = XML.SubElement(pdefp, 'parameterDefinitions')
            for param in parameters:
                self._dispatch('parameter', 'parameters',
                               parser, pdefs, param)
