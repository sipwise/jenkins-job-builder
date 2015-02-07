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
Reporters are like publishers but only applicable to Maven projets.

**Component**: reporters
  :Macro: reporter
  :Entry Point: jenkins_jobs.reporters

Example::

  job:
    name: test_job
    project-type: maven

    reporters:
      - email:
          recipients: breakage@example.com
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.errors import JenkinsJobsException


def email(parser, xml_parent, data):
    """yaml: email
    Email notifications on build failure.

    :arg str recipients: Recipient email addresses
    :arg bool notify-every-unstable-build: Send an email for every
      unstable build (default true)
    :arg bool send-to-individuals: Send an email to the individual
      who broke the build (default false)

    Example::

      reporters:
        - email:
            recipients: breakage@example.com
    """

    mailer = XML.SubElement(xml_parent,
                            'hudson.maven.reporters.Mailer')
    XML.SubElement(mailer, 'recipients').text = data['recipients']

    # Note the logic reversal (included here to match the GUI
    if data.get('notify-every-unstable-build', True):
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'false'
    else:
        XML.SubElement(mailer, 'dontNotifyEveryUnstableBuild').text = 'true'
    XML.SubElement(mailer, 'sendToIndividuals').text = str(
        data.get('send-to-individuals', False)).lower()
    # TODO: figure out what this is:
    XML.SubElement(mailer, 'perModuleEmail').text = 'true'


def findbugs(parser, xml_parent, data):
    """yaml: findbugs
    FindBugs reporting for builds

    :arg bool rank-priority: Use rank as priority (default: false)
    :arg str include-files: Comma separated list of files to include.
                            (Optional)
    :arg str exclude-files: Comma separated list of files to exclude.
                            (Optional)
    :arg bool run-always: Weather or not to run plug-in on failed builds.
                          (default: false)
    :arg int healthy-threshold: Percent threshhold for a healthy build.
                                (optional)
    :arg int unhealthy-threshold: Percent threshold for an unhealthy build.
                                  (optional)
    :arg str health-priorities: Determines which warning priorities should be
                                considered when evaluating the build health.
                                options: low, normal, high (default: low)
    :arg bool compute-new-warnings: Compute new warnings based on reference
                                    build. (Default: false)
    :arg bool use-delta-values: Use delta for new warnings. (Default: false)
    :arg bool use-previous-build: Use previous build as reference.
                                  (Default: false)
    :arg bool use-stable-only: Use stable builds only as reference.
                               (Default: false)
    :arg dict thresholds:
        :thresholds:
            * **unstable-all** (`int`) - Unstable all threshold. (Optional)
            * **unstable-high** (`int`) - Unstable high threshold. (Optional)
            * **unstable-normal** (`int`) - Unstable normal threshold.
                                            (Optional)
            * **unstable-low** (`int`) - Unstable low threshold. (Optional)
            * **failed-all** (`int`) - Failed all threshold. (Optional)
            * **failed-high** (`int`) - Failed high threshold. (Optional)
            * **failed-normal** (`int`) - Failed normal threshold. (Optional)
            * **failed-low** (`int`) - Failed low threshold. (Optional)
            * **unstable-new-all** (`int`) - Unstable new all threshold.
                                             (Optional)
            * **unstable-new-high** (`int`) - Unstable new high threshold.
                                              (Optional)
            * **unstable-new-normal** (`int`) - Unstable new normal threshold.
                                                (Optional)
            * **unstable-new-low** (`int`) - Unstable new low threshold.
                                             (Optional)
            * **failed-new-all** (`int`) - Failed new all threshold.
                                           (Optional)
            * **failed-new-high** (`int`) - Failed new high threshold.
                                            (Optional)
            * **failed-new-normal** (`int`) - Failed new normal threshold.
                                              (Optional)
            * **failed-new-low** (`int`) - Failed new low threshold.
                                           (Optional)

    Minimal Example:

    .. literalinclude::  /../../tests/reporters/fixtures/findbugs-minimal.yaml

    Full Example:

    .. literalinclude::  /../../tests/reporters/fixtures/findbugs01.yaml

    """
    findbugs = XML.SubElement(xml_parent,
                              'hudson.plugins.findbugs.FindBugsReporter')
    findbugs.set('plugin', 'findbugs')

    supported_health_priorities = ['low', 'normal', 'high']

    # Health related
    healthy_threshold = str(data.get('healthy-threshold', ''))
    XML.SubElement(findbugs, 'healthy').text = healthy_threshold
    unhealthy_threshold = str(data.get('unhealthy-threshold', ''))
    XML.SubElement(findbugs, 'unHealthy').text = unhealthy_threshold
    XML.SubElement(findbugs, 'pluginName').text = '[FINDBUGS] '
    health_priorities = data.get('health-priorities', 'low').lower()
    if health_priorities not in supported_health_priorities:
        raise jenkins_jobs.errors.JenkinsJobsException(
            "Choice should be one of the following options: %s." %
            ", ".join(supported_health_priorities))
    XML.SubElement(findbugs, 'thresholdLimit').text = health_priorities
    run_always = str(data.get('run-always', False)).lower()
    XML.SubElement(findbugs, 'canRunOnFailed').text = run_always

    compute_new_warnings = data.get('compute-new-warnings', False)
    XML.SubElement(findbugs, 'dontComputeNew').text = str(
        not compute_new_warnings).lower()

    use_delta_values = str(data.get('use-delta-values', False)).lower()
    use_previous_build = str(data.get('use-previous-build', False)).lower()
    use_stable_only = str(data.get('use-stable-only', False)).lower()
    if not compute_new_warnings:
        use_delta_values = 'false'
        use_previous_build = 'false'
        use_stable_only = 'false'
    XML.SubElement(findbugs, 'useDeltaValues').text = use_delta_values
    XML.SubElement(findbugs,
                   'usePreviousBuildAsReference').text = use_previous_build
    XML.SubElement(findbugs,
                   'useStableBuildAsReference').text = use_stable_only

    # Status Thresholds
    if 'thresholds' in data:
        tdata = data['thresholds']
        thresholds = XML.SubElement(findbugs, 'thresholds')
        thresholds.set('plugin', 'analysis-core')

        unstable_all = str(tdata.get('unstable-all', ''))
        XML.SubElement(thresholds, 'unstableTotalAll').text = unstable_all
        unstable_high = str(tdata.get('unstable-high', ''))
        XML.SubElement(thresholds, 'unstableTotalHigh').text = unstable_high
        unstable_normal = str(tdata.get('unstable-high', ''))
        XML.SubElement(thresholds,
                       'unstableTotalNormal').text = unstable_normal
        unstable_low = str(tdata.get('unstable-low', ''))
        XML.SubElement(thresholds, 'unstableTotalLow').text = unstable_low

        failed_all = str(tdata.get('failed-all', ''))
        XML.SubElement(thresholds, 'failedTotalAll').text = failed_all
        failed_high = str(tdata.get('failed-high', ''))
        XML.SubElement(thresholds, 'failedTotalHigh').text = failed_high
        failed_normal = str(tdata.get('failed-normal', ''))
        XML.SubElement(thresholds, 'failedTotalNormal').text = failed_normal
        failed_low = str(tdata.get('failed-low', ''))
        XML.SubElement(thresholds, 'failedTotalLow').text = failed_low

        if compute_new_warnings:
            unstable_new_all = str(tdata.get('unstable-new-all', ''))
            XML.SubElement(thresholds, 'unstableNewAll').text = \
                unstable_new_all
            unstable_new_high = str(tdata.get('unstable-new-high', ''))
            XML.SubElement(thresholds, 'unstableNewHigh').text = \
                unstable_new_high
            unstable_new_normal = str(tdata.get('unstable-new-high', ''))
            XML.SubElement(thresholds,
                           'unstableNewNormal').text = unstable_new_normal
            unstable_new_low = str(tdata.get('unstable-new-low', ''))
            XML.SubElement(thresholds, 'unstableNewLow').text = \
                unstable_new_low

            failed_new_all = str(tdata.get('failed-new-all', ''))
            XML.SubElement(thresholds, 'failedNewAll').text = \
                failed_new_all
            failed_new_high = str(tdata.get('failed-new-high', ''))
            XML.SubElement(thresholds, 'failedNewHigh').text = \
                failed_new_high
            failed_new_normal = str(tdata.get('failed-new-normal', ''))
            XML.SubElement(thresholds, 'failedNewNormal').text = \
                failed_new_normal
            failed_new_low = str(tdata.get('failed-new-low', ''))
            XML.SubElement(thresholds, 'failedNewLow').text = \
                failed_new_low

    # General Options
    rank_priority = str(data.get('rank-priority', False)).lower()
    XML.SubElement(findbugs, 'isRankActivated').text = rank_priority
    include_files = data.get('include-files', '')
    XML.SubElement(findbugs, 'includePattern').text = include_files
    exclude_files = data.get('exclude-files', '')
    XML.SubElement(findbugs, 'excludePattern').text = exclude_files


class Reporters(jenkins_jobs.modules.base.Base):
    sequence = 55

    component_type = 'reporter'
    component_list_type = 'reporters'

    def gen_xml(self, parser, xml_parent, data):
        if 'reporters' not in data:
            return

        if xml_parent.tag != 'maven2-moduleset':
            raise JenkinsJobsException("Reporters may only be used for Maven "
                                       "modules.")

        reporters = XML.SubElement(xml_parent, 'reporters')

        for action in data.get('reporters', []):
            self.registry.dispatch('reporter', parser, reporters, action)
