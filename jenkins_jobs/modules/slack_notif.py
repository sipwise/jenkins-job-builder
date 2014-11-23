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
Enable Slack notifications of build execution.

Requires the Jenkins `Slack Plugin.
<https://github.com/jenkinsci/slack-plugin>`_

:Parameters:
  * **enabled** *(bool)*: general cut off switch. If not explicitly set to
    ``true``, no slack parameters are written to XML.
  * **room** *(str)*: name of Slack room to post messages to
  * **notify-start** *(bool)*: post messages about build start event
  * **notify-success** *(bool)*: post messages about successful build event
  * **notify-aborted** *(bool)*: post messages about aborted build event
  * **notify-not-built** *(bool)*: post messages about build set to NOT_BUILT
    status. This status code is used in a
    multi-stage build (like maven2) where a problem in earlier stage prevented
    later stages from building.
  * **notify-unstable** *(bool)*: post messages about unstable build event
  * **notify-failure** *(bool)*:  post messages about build failure event
  * **notify-back-to-normal** *(bool)*: post messages about build being back to

Example:

.. literalinclude:: /../../tests/slack/fixtures/slack001.yaml
   :language: yaml

"""

# Enabling slack notifications on a job requires specifying the slack
# config in job properties, and adding the slack notifier to the job's
# publishers list.
# The publisher configuration contains extra details not specified per job:
# - the slack authorisation token.
# - the jenkins server url.
# - a default room name/id.
# This complicates matters somewhat since the sensible place to store these
# details is in the global config file.
# The global config object is therefore passed down to the registry object,
# and this object is passed to the Slack() class initialiser.

import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.errors
import logging
from six.moves import configparser

logger = logging.getLogger(__name__)


class Slack(jenkins_jobs.modules.base.Base):
    sequence = 80

    def __init__(self, registry):
        self.authToken = None
        self.buildServerUrl = None
        self.registry = registry

    def _load_global_data(self):
        """Load data from the global config object.
           This is done lazily to avoid looking up the '[slack]' section
           unless actually required.
        """
        if (not self.authToken):
            try:
                self.authToken = self.registry.global_config.get(
                    'slack', 'token')
                # Require that the authtoken is non-null
                if not self.authToken:
                    raise jenkins_jobs.errors.JenkinsJobsException(
                        "Slack authtoken must not be a blank string")
            except (configparser.NoSectionError,
                    jenkins_jobs.errors.JenkinsJobsException) as e:
                logger.fatal("The configuration file needs a slack section" +
                             " containing authtoken:\n{0}".format(e))
                raise e
            try:
                self.teamDomain = self.registry.global_config.get(
                    'slack', 'team_domain')
                # Require that the teamDomain is non-null
                if self.teamDomain == '':
                    raise jenkins_jobs.errors.JenkinsJobsException(
                        "Slack teamDomain must not be a blank string")
            except (configparser.NoSectionError,
                    jenkins_jobs.errors.JenkinsJobsException) as e:
                logger.fatal("The configuration file needs a slack section" +
                             " containing teamDomain:\n{0}".format(e))
                raise e
            self.buildServerUrl = self.registry.global_config.get('jenkins',
                                                                  'url')

    def gen_xml(self, parser, xml_parent, data):
        slack = data.get('slack')
        if not slack or not slack.get('enabled', True):
            return
        if 'room' not in slack:
            raise jenkins_jobs.errors.YAMLFormatError(
                "Missing slack 'room' specifier")
        self._load_global_data()

        properties = xml_parent.find('properties')
        if properties is None:
            properties = XML.SubElement(xml_parent, 'properties')
        pdefslack = XML.SubElement(properties,
                                   'jenkins.plugins.slack.'
                                   'SlackNotifier_-SlackJobProperty')
        XML.SubElement(pdefslack, 'room').text = '#' + slack['room']
        XML.SubElement(pdefslack, 'startNotification').text = str(
            slack.get('notify-start', False)).lower()
        XML.SubElement(pdefslack, 'notifySuccess').text = str(
            slack.get('notify-success', False)).lower()
        XML.SubElement(pdefslack, 'notifyAborted').text = str(
            slack.get('notify-aborted', False)).lower()
        XML.SubElement(pdefslack, 'notifyNotBuilt').text = str(
            slack.get('notify-not-built', False)).lower()
        XML.SubElement(pdefslack, 'notifyUnstable').text = str(
            slack.get('notify-unstable', False)).lower()
        XML.SubElement(pdefslack, 'notifyFailure').text = str(
            slack.get('notify-failure', False)).lower()
        XML.SubElement(pdefslack, 'notifyBackToNormal').text = str(
            slack.get('notify-back-to-normal', False)).lower()

        publishers = xml_parent.find('publishers')
        if publishers is None:
            publishers = XML.SubElement(xml_parent, 'publishers')
        slackpub = XML.SubElement(publishers,
                                  'jenkins.plugins.slack.SlackNotifier')
        XML.SubElement(slackpub, 'teamDomain').text = self.teamDomain
        XML.SubElement(slackpub, 'buildServerUrl').text = self.buildServerUrl
        XML.SubElement(slackpub, 'authToken').text = self.authToken
        # The room specified here is the default room.  The default is
        # redundant in this case since a room must be specified.  Leave empty.
        XML.SubElement(slackpub, 'room').text = ''
