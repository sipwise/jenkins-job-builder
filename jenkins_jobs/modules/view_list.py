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
The view list module handles creating Jenkins List views.

To create a list view specify ``list`` in the ``view-type`` attribute
to the :ref:`View` definition.

:View Parameters:
    * **jobnames** (`list`): List of jobs to be included.
    * **columns** (`list`): List of columns to be shown in view.
    * **regex** (`str`): . Regular expression for selecting jobs
      (optional)
    * **recurse** (`bool`): Recurse in subfolders.(default false)
    * **statusfilter** (`bool`): Filter job list by enabled/disabled
      status. (optional)

Example:

    .. literalinclude:: /../../tests/general/fixtures/list_view001.yaml

Example:

    .. literalinclude:: /../../tests/general/fixtures/list_view002.yaml
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base_view

COLUMN_DICT = {
    'status': 'hudson.views.StatusColumn',
    'weather': 'hudson.views.WeatherColumn',
    'job': 'hudson.views.JobColumn',
    'last-success': 'hudson.views.LastSuccessColumn',
    'last-failure': 'hudson.views.LastFailureColumn',
    'last-duration': 'hudson.views.LastDurationColumn',
    'build-button': 'hudson.views.BuildButtonColumn',
    'last-stable': 'hudson.views.LastStableColumn',
}


class List(jenkins_jobs.modules.base_view.BaseView):
    sequence = 0

    def root_xml(self, data):
        root = XML.Element('hudson.model.ListView')

        root = self.gen_view(data=data, root=root)

        jn_xml = XML.SubElement(root, 'jobNames')
        jobnames = data.get('jobnames', None)
        XML.SubElement(jn_xml, 'comparator', {'class':
                       'hudson.util.CaseInsensitiveComparator'})
        if jobnames is not None:
            for jobname in jobnames:
                XML.SubElement(jn_xml, 'string').text = str(jobname)
        XML.SubElement(root, 'jobFilters')

        c_xml = XML.SubElement(root, 'columns')
        columns = data.get('columns', [])
        for column in columns:
            if column in COLUMN_DICT:
                XML.SubElement(c_xml, COLUMN_DICT[column])

        regex = data.get('regex', None)
        if regex is not None:
            XML.SubElement(root, 'includeRegex').text = regex

        recurse = data.get('recurse', False)
        R_element = XML.SubElement(root, 'recurse')
        R_element.text = 'true' if recurse else 'false'

        statusfilter = data.get('statusfilter', None)
        if statusfilter is not None:
            SF_element = XML.SubElement(root, 'statusFilter')
            SF_element.text = 'true' if statusfilter else 'false'

        return root
