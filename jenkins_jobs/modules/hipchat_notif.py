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

# Jenkins Job module for HipChat notifications
# - job:
#     hipchat:
#       enabled: <true|false>
#       room:  <hipchat room name>
#       start-notify: <true|false>

# Enabling hipchat notifications on a job requires specifying the hipchat
# config in job properties, and adding the hipchat notifier to the job's
# publishers list.
# The publisher configuration contains extra details not specified per job:
#   - the hipchat authorisation token.
#   - the jenkins server url.
#   - a default room name/id.
# This complicates matters somewhat since the sensible place to store these
# details is in the global config file.
# The global config object is therefore passed down to the registry object,
# and this object is passed to the HipChat() class initialiser.

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.errors
import logging
import ConfigParser

logger = logging.getLogger(__name__)


def hipchat_property(parser, xml_parent, data):
    pdefhip = XML.SubElement(xml_parent,
              'jenkins.plugins.hipchat.HipChatNotifier_-HipChatJobProperty')
    XML.SubElement(pdefhip, 'room').text = data['room']
    XML.SubElement(pdefhip, 'startNotification').text = str(
                                  data.get('start-notify', 'false')).lower()


def hipchat_publisher(parser, xml_parent, data):
    hippub = XML.SubElement(xml_parent,
                       'jenkins.plugins.hipchat.HipChatNotifier')
    XML.SubElement(hippub, 'jenkinsUrl').text = data['jenkins_url']
    XML.SubElement(hippub, 'authToken').text = data['authtoken']
    XML.SubElement(hippub, 'room').text = data['default_room_id']


class HipChat(jenkins_jobs.modules.base.Base):
    sequence = 15

    def __init__(self, registry):
        self.authToken = None
        self.jenkinsUrl = None
        self.registry = registry

    def _load_global_data(self):
        """Load data from the global config object.
           This is done lazily to avoid looking up the '[hipchat]' section
           unless actually required.
        """
        if(not self.authToken):
            # Verify that the config object in the registry is of type
            # ConfigParser (it could possibly be a regular 'dict' object which
            # doesn't have the right get() method).
            if(not isinstance(self.registry.global_config,
                    ConfigParser.ConfigParser)):
                raise jenkins_jobs.errors.JenkinsJobsException(
                           'HipChat requires a config object in the registry.')
            self.authToken = self.registry.global_config.get(
                               'hipchat', 'authtoken')
            self.jenkinsUrl = self.registry.global_config.get('jenkins', 'url')

    def handle_data(self, parser):
        """Take a job's hipchat definition, add in the details from the global
           config object, and push to the 'properties' and 'publishers' lists.
        """
        changed = False
        jobs = (parser.data.get('job', {}).values() +
                parser.data.get('job-template', {}).values())
        for job in jobs:
            hc_props = job.get('hipchat')
            if(not hc_props or not hc_props.get('enabled', True)):
                continue
            if('room' not in hc_props):
                raise jenkins_jobs.errors.YAMLFormatError(
                  "Job '{0}' missing hipchat 'room' specifier".format(
                        job['name']))
            self._load_global_data()
            # Use an empty value for default_room_id - it is only used in
            # the publisher section as the default room.  The default is
            # redundant in this case since a room must be specified.
            hc_props['default_room_id'] = ''
            hc_props['authtoken'] = self.authToken
            hc_props['jenkins_url'] = self.jenkinsUrl
            hc_props = {'hipchat': hc_props}
            job.setdefault('properties', []).append(hc_props)
            job.setdefault('publishers', []).append(hc_props)
            # Delete the toplevel 'hipchat' entry to prevent reprocessing.
            del job['hipchat']
            changed = True

        return changed
