# Copyright 2015 Openstack Foundation

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
These are parameters that are common to every Jenkins View.

:View Parameters:
    * **name** (`str`):
      The name of the view

    * **description** (`str`):
      A description of the view (optional)

    * **filter-executors** (`bool`):
      Show only executors that can execute the included views.
      (default false)

    * **filter-queue** (`bool`):
      Show only included jobs in builder queue. (default false)
"""

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class BaseView(jenkins_jobs.modules.base.Base):
    """
    A base class for a Jenkins Job Builder View modules

    Inherits from ``jenkins_jobs.modules.base.Base``.
    """

    def gen_view(self, data, root):
        """This method handles parameters that are common to all views. Create
        a new XML element tree and then call this method to handle creating
        the general structure for a view tree and then add more elements as
        needed in the view module.

        :arg dict data: the YAML data structure
        :arg Element root: the XML tree root element
        """

        XML.SubElement(root, 'name').text = data['name']
        desc_text = data.get('description', None)
        if desc_text is not None:
            XML.SubElement(root, 'description').text = desc_text

        filterExecutors = data.get('filter-executors', False)
        FE_element = XML.SubElement(root, 'filterExecutors')
        FE_element.text = 'true' if filterExecutors else 'false'

        filterQueue = data.get('filter-queue', False)
        FQ_element = XML.SubElement(root, 'filterQueue')
        FQ_element.text = 'true' if filterQueue else 'false'

        XML.SubElement(root, 'properties',
                       {'class': 'hudson.model.View$PropertyList'})

        return root
