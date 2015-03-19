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
The Notifications module allows you to configure Jenkins to notify
other applications about various build phases.  It requires the
Jenkins notification plugin.

**Component**: notifications
  :Macro: notification
  :Entry Point: jenkins_jobs.notifications

Example::

  job:
    name: test_job

    notifications:
      - http:
          url: http://example.com/jenkins_endpoint
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


def http_endpoint(parser, xml_parent, data):
    """yaml: http
    Defines an HTTP notification endpoint.
    Requires the Jenkins :jenkins-wiki:`Notification Plugin
    <Notification+Plugin>`.

    :arg str protocol: protocol to use for sending notification messages,
        HTTP, TCP or UDP (default HTTP)
    :arg str format: notification payload format, JSON or XML (default JSON)
    :arg str url: URL to send notifications to. It takes the form of
        "http://host" for HTTP protocol, and "host:port" for TCP and UDP
        protocols (required)
    :arg str event: job events that trigger notifications started, completed,
        finzlized or all (default all)
    :arg int timeout: timeout in milliseconds for sending notification request
        (default 30000)
    :arg int loglines: number of loglines to send in payload (default 0)

    Example::

      notifications:
        - http:
            url: http://example.com/jenkins_endpoint
    """
    endpoint_element = XML.SubElement(xml_parent,
                                      'com.tikal.hudson.plugins.notification.'
                                      'Endpoint')
    XML.SubElement(endpoint_element, 'protocol').text = data.get(
        'protocol', 'HTTP').upper()
    XML.SubElement(endpoint_element, 'format').text = data.get(
        'format', 'JSON').upper()
    XML.SubElement(endpoint_element, 'url').text = data['url']
    XML.SubElement(endpoint_element, 'event').text = data.get('event', 'all')
    XML.SubElement(endpoint_element, 'timeout').text = str(
        data.get('timeout', 30000))
    XML.SubElement(endpoint_element, 'loglines').text = str(
        data.get('loglines', 0))


class Notifications(jenkins_jobs.modules.base.Base):
    sequence = 22

    component_type = 'notification'
    component_list_type = 'notifications'

    def gen_xml(self, parser, xml_parent, data):
        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')

        notifications = data.get('notifications', [])
        if notifications:
            notify_element = XML.SubElement(properties,
                                            'com.tikal.hudson.plugins.'
                                            'notification.'
                                            'HudsonNotificationProperty')
            endpoints_element = XML.SubElement(notify_element, 'endpoints')

            for endpoint in notifications:
                self.registry.dispatch('notification',
                                       parser, endpoints_element, endpoint)
