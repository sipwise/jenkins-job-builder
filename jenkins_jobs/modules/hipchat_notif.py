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
# config in job properties, and adding the hipchat notifyier to the job's
# publishers list.
# The publisher configuration requires the hipchat authorisation token as well
# as the room id (and the jenkins server url for some reason).  
# This complicates matters quite a bit:
#  - The HipChat class needs access to the global config object (where the
#    hipchat authtoken & jenkins url are stored.
#  - A lookup needs to be done to the hipchat service to determine the room id
#    for the specified room name.
#
# The global config access is especially kludgy, and should be given proper
# thought and reworked.

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.errors
import logging
import hipchat

logger = logging.getLogger(__name__)

class HipChat(jenkins_jobs.modules.base.Base):
    sequence = 15
    def __init__(self, registry):
        self.client = None
        
    def _connect(self):
        # Kludge alert - delving directly into __main__ namespace to 
        # get at the config object.
        if(not self.client):
            import __main__
            logger.debug("Config obj: {0}".format(__main__.config))
            self.authToken = __main__.config.get('hipchat', 'authtoken')
            # Not sure why, but the jenkins server url is included in the
            # hipchat publisher section.  
            self.jenkinsUrl = __main__.config.get('jenkins', 'url')
            
            import hipchat
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
            logger.debug("HipChat room '{0}' => {1}".format(
                                 hc_props['room'], hc_props['room_id']))
            hc_props['authtoken'] = self.authToken
            hc_props['jenkins_url'] = self.jenkinsUrl
            hc_props = { 'hipchat': hc_props }
            job.setdefault('properties', []).append(hc_props)
            job.setdefault('publishers', []).append(hc_props)
            # Delete the toplevel 'hipchat' entry to prevent reprocessing
            del job['hipchat']
            changed = True
            
        return changed
