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
# The publisher configuration requires the hipchat authorisation token as well
# as the room id (and the jenkins server url for some reason).  
# This complicates matters quite a bit:
#  - The HipChat class needs access to the global config object (where the
#    hipchat authtoken & jenkins url are stored).
#  - A lookup needs to be done to the hipchat service to determine the room id
#    for the specified room name.

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
    XML.SubElement(hippub, 'room').text = data['room_id']
                                  
class HipChat(jenkins_jobs.modules.base.Base):
    sequence = 15
    def __init__(self, registry):
        self.client = None
        self.registry = registry
        
    def _connect(self):
        if(not self.client):
            # Verify that the config object in the registry is of type
            # ConfigParser (it could possibly be a regular 'dict' object which
            # doesn't have the right get() method).
            if(not isinstance(self.registry.global_config, 
                ConfigParser.ConfigParser)):
                    raise jenkins_jobs.errors.JenkinsJobException(
                           'HipChat requires a config object in the registry.')
            self.authToken = self.registry.global_config.get(
                               'hipchat', 'authtoken')
            # Save the jenkins server url also (it is required in the
            # hipchat publisher section for some reason).
            self.jenkinsUrl = self.registry.global_config.get('jenkins', 'url')
            try:
                import hipchat
            except ImportError:
                logger.error(
                   "Use of hipchat notifications requires the "
                   "'python-simple-hipchat' module: "
                   "pip install python-simple-hipchat")
                raise
            logger.debug("Connecting to HipChat service (token={0})".format(
                         self.authToken))
            self.client = hipchat.HipChat(token=self.authToken)
            self.rooms =  dict( [ ( m['name'], m['room_id'] )
                                for m in self.client.list_rooms()['rooms']] )
    
    def handle_data(self, parser):
        changed = False
        jobs = (parser.data.get('job', {}).values() +
                parser.data.get('job-template', {}).values())
        for job in jobs:
            hc_props = job.get('hipchat')
            if(not hc_props or not hc_props.get('enabled', True)):
                continue
            if('room' not in hc_props):
                raise jenkins_jobs.errors.YAMLFormatError (
                  "Job '{0}' missing hipchat 'room' specifier".format(
                        job['name']))
            self._connect()
            if(hc_props['room'] not in self.rooms):
                raise jenkins_jobs.errors.JenkinsJobsException(
                        "Cannot find hipchat room '{0}' (job {1})".format(
                            hc_props['room'], job['name']))
            hc_props['room_id'] = str(self.rooms[hc_props['room']])
            logger.debug("Room '{0}' => {1}".format(
                                 hc_props['room'], hc_props['room_id']))
            hc_props['authtoken'] = self.authToken
            hc_props['jenkins_url'] = self.jenkinsUrl
            hc_props = { 'hipchat': hc_props }
            job.setdefault('properties', []).append(hc_props)
            job.setdefault('publishers', []).append(hc_props)
            # Delete the toplevel 'hipchat' entry to prevent reprocessing.
            del job['hipchat']
            changed = True
            
        return changed
