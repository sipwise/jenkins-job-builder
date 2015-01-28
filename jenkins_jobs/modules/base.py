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

# Base class for a jenkins_jobs module

import xml.etree.ElementTree as XML


def add_nonblank_xml_subelement(parent, tag, value):
    """
    Adds an XML SubElement with the name tag to parent if value is a non-empty
    string
    """
    if value is not None and value != '':
        XML.SubElement(parent, tag).text = value


class Base(object):
    """
    A base class for a Jenkins Job Builder Module.

    The module is initialized before any YAML is parsed.

    :arg ModuleRegistry registry: the global module registry.
    """

    #: The sequence number for the module.  Modules are invoked in the
    #: order of their sequence number in order to produce consistently
    #: ordered XML output.
    sequence = 10

    #: The component type for components of this module.  This will be
    #: used to look for macros (they are defined singularly, and should
    #: not be plural).
    #: Set both component_type and component_list_type to None if module
    #: doesn't have components.
    component_type = None

    #: The component list type will be used to look up possible
    #: implementations of the component type via entry points (entry
    #: points provide a list of components, so it should be plural).
    #: Set both component_type and component_list_type to None if module
    #: doesn't have components.
    component_list_type = None

    def __init__(self, registry):
        self.registry = registry

    def handle_data(self, parser):
        """This method is called before any XML is generated.  By
        overriding this method, the module may manipulate the YAML
        data structure on the parser however it likes before any XML
        is generated.  If it has changed the data structure at all, it
        must return ``True``, otherwise, it must return ``False``.

        :arg YAMLParser parser: the global YAML Parser
        :rtype: boolean
        """

        return False

    def gen_xml(self, parser, xml_parent, data):
        """Update the XML element tree based on YAML data.  Override
        this method to add elements to the XML output.  Create new
        Element objects and add them to the xml_parent.  The YAML data
        structure must not be modified.

        :arg YAMLParser parser: the global YAML Parser
        :arg Element xml_parent: the parent XML element
        :arg dict data: the YAML data structure
        """

        pass

    def render_macro(self, parser, data):
        """Render the macros based on YAML data.

        :arg YAMLParser parser: the global YAML Parser
        :arg dict data: the YAML data structure
        """

        component_data = dict()
        data_list = list()
        if (self.component_list_type is not None and
                self.component_type is not None):
            for wrap in data.get(self.component_list_type, []):
                wrap_name, wrap_data = self.registry.dismacro(
                    self.component_type, parser, wrap)
                if isinstance(wrap, dict):
                    data_list.append({wrap_name: wrap_data})
                else:
                    data_list.append(wrap_data)

            if data_list:
                component_data[self.component_list_type] = data_list
        return component_data
