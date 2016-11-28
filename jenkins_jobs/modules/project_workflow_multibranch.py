# -*- coding: utf-8 -*-
# Copyright (C) 2015 Joost van der Griendt <joostvdg@gmail.com>
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
The workflow Project module handles creating Jenkins workflow projects.
You may specify ``workflow-multibranch`` in the ``project-type`` attribute of
the :ref:`Job` definition.

You can add an SCM with the script-path, but for now only
GIT and GITHUB is supported.

Requires the Jenkins :jenkins-wiki:`Workflow Plugin <Workflow+Plugin>`.

In order to use it for job-template you have to escape the curly braces by
doubling them in the script: { -> {{ , otherwise it will be interpreted by the
python str.format() command.

:Job Parameters:
    * **timer-trigger** (`str`): The timer spec for when the jobs
        should be triggered.
    * **env-properties** (`str`): Environment variables. (optional)
    * **periodic-folder-spec** (`str`): The timer spec for when the repository
        should be checked for branches. (optional)
    * **periodic-folder-interval** (`str`): Interval for when the folder
        should be checked.
    * **prune-dead-branches** (`bool`): If dead branches upon check should
        result in their job being dropped. (defaults to true) (optional)
    * **number-to-keep** (`int`): How many builds should be
        kept. (defaults to -1, all) (optional)
    * **days-to-keep** (`int`): For how many days should a build
        be kept. (defaults to -1, forever) (optional)
    * **scm** (`str`): The SCM definition. Currently only `git` or `github`
        as SCM is supported, use this as sub-structure of scm.

    * **git** (`str`): Use this as sub-structure of scm when using git.
    * **url** (`str`): The git url.
    * **credentials-id** (`str`): The credentialsId to use to connect
        to the GIT URL.
    * **includes** (`str`): Which branches should be
        included. (defaults to *, all)  (optional)
    * **excludes** (`str`): Which branches should be
        excluded. (defaults to empty, none)  (optional)
    * **ignore-on-push-notifications** (`bool`): If a job should
        not trigger upon push notifications. (defaults to
        false) (optional)

    * **github** (`str`): Use this as sub-structure of scm when using github.
    * **repo** (`str`): The github repo.
    * **repo-owner** (`str`): The github repo owner.
    * **scan-credentials-id** (`str`): The credentialsId to use
        to scan github.
    * **checkout-credentials-id** (`str`): The credentialsId to use
        to checkout from github.  (defaults to same as scan-credentials-id)
        (optional)
    * **includes** (`str`): Which branches should be
        included. (defaults to *, all)  (optional) be excluded. (defaults
        to empty, none)  (optional)
    * **api-uri** (`str`): The github api uri (for
        hosted/on-site github).  (optional)
    * **build-origin-branch** (`bool`) Build origin branches.  (defaults
        to true) (optional)
    * **build-origin-branch-with-pr** (`bool`) Build origin
        branches also filed as PRs.  (defaults to true) (optional)
    * **build-origin-pr-merge** (`bool`) Build origin PRs (merged with base
        branch).  (defaults to false) (optional)
    * **build-origin-pr-head** (`bool`) Build origin PRs (unmerged
        head).  (defaults to false) (optional)
    * **build-fork-pr-merge** (`bool`) Build fork PRs (merged
        with base branch).  (defaults to true) (optional)
    * **build-fork-pr-head** (`bool`) Build fork
        PRs (unmerged head).  (defaults to false) (optional)

    * **bitbucket** (`str`): Use this with bitbucket SCM plugin.
    * **repo** (`str`): The repo.
    * **repo-owner** (`str`): Bitbucket project/repo owner.
    * **scan-credentials-id** (`str`): The credentialsId to use
        to scan github. (defaults to 'SAME')
    * **checkout-credentials-id** (`str`): The credentialsId to use
        to checkout from bitbucket.  (defaults to empty, none)
        (optional)
    * **includes** (`str`): Which branches should be
        included. (defaults to *, all)  (optional) be excluded. (defaults
        to empty, none)  (optional)
    * **bitbucket-server-url** (`str`) Bitbucket server URL, to be set when
        used with Bitbucket Server. (defaults to empty, none) (optional)
    * **auto-register-webhook** (`bool`) Register webhook in Bitbucket.
        (defaults to false) (optional)
    * **ssh-port** (`int`) Bitbucket ssh port. (defaults to empty, none)
        (optional)
    * **repository-type** (`str`) Bitbucket repo type. (defaults to 'GIT')
        (optional)


Job with inline script example:

.. literalinclude::
   /../../tests/yamlparser/fixtures/project_pipeline_multibranch_template001.yml

"""
import logging
import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import uuid

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.modules import helpers

logger = logging.getLogger(str(__name__))


class WorkflowMultiBranch(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        xml_parent = XML.Element(
            ('org.jenkinsci.plugins.workflow.'
             'multibranch.WorkflowMultiBranchProject'))
        xml_parent.attrib['plugin'] = 'workflow-multibranch'

        if 'multibranch' not in data:
            return xml_parent

        project_def = data['multibranch']

        properties = XML.SubElement(xml_parent, 'properties')
        folder_credentials_provider = XML.SubElement(
            properties,
            ('com.cloudbees.hudson.plugins.folder.properties'
             '.FolderCredentialsProvider_-FolderCredentialsProperty'))
        folder_credentials_provider.attrib['plugin'] = 'cloudbees-folder'
        domain_credentials_map = XML.SubElement(
            folder_credentials_provider, 'domainCredentialsMap')
        domain_credentials_map.attrib['class'] = ('hudson.util.'
                                                  'CopyOnWriteMap$Hash')
        entry = XML.SubElement(domain_credentials_map, 'entry')
        domain = XML.SubElement(
            entry, 'com.cloudbees.plugins.credentials.domains.Domain')
        domain.attrib['plugin'] = 'credentials'
        XML.SubElement(domain, 'specifications')
        XML.SubElement(entry, 'java.util.concurrent.CopyOnWriteArrayList')

        if 'env-properties' in data['multibranch']:
            env_properties_parent = XML.SubElement(
                properties,
                ('com.cloudbees.hudson.plugins.folder.'
                 'properties.EnvVarsFolderProperty'))
            env_properties_parent.attrib['plugin'] = 'cloudbees-folders-plus'
            env_properties = XML.SubElement(
                env_properties_parent, 'properties')
            env_properties.text = project_def['env-properties']

        views = XML.SubElement(xml_parent, 'views')
        allView = XML.SubElement(views, 'hudson.model.AllView')
        owner = XML.SubElement(allView, 'owner')
        owner.attrib['class'] = ('org.jenkinsci.plugins.'
                                 'workflow.multibranch.'
                                 'WorkflowMultiBranchProject')
        owner.attrib['reference'] = '../../..'
        all_view_name = XML.SubElement(allView, 'name')
        all_view_name.text = 'All'
        all_view_filter_executors = XML.SubElement(allView, 'filterExecutors')
        all_view_filter_executors.text = 'false'
        all_view_filter_queue = XML.SubElement(allView, 'filterQueue')
        all_view_filter_queue.text = 'false'
        all_view_properties = XML.SubElement(allView, 'properties')
        all_view_properties.attrib['class'] = 'hudson.model.View$PropertyList'

        views_tab_bar = XML.SubElement(xml_parent, 'viewsTabBar')
        views_tab_bar.attrib['class'] = 'hudson.views.DefaultViewsTabBar'

        health_metrics = XML.SubElement(xml_parent, 'healthMetrics')
        health_metrics_plugin = XML.SubElement(
            health_metrics,
            ('com.cloudbees.hudson.plugins.'
             'folder.health.WorstChildHealthMetric'))
        health_metrics_plugin.attrib['plugin'] = 'cloudbees-folder'

        icon = XML.SubElement(xml_parent, 'icon')
        icon.attrib['class'] = ('com.cloudbees.hudson.plugins'
                                '.folder.icons.StockFolderIcon')
        icon.attrib['plugin'] = 'cloudbees-folder'

        orphaned_item_strategy = XML.SubElement(
            xml_parent, 'orphanedItemStrategy')
        orphaned_item_strategy.attrib['class'] = (
            'com.cloudbees.hudson.plugins.folder.computed.'
            'DefaultOrphanedItemStrategy')
        orphaned_item_strategy.attrib['plugin'] = 'cloudbees-folder'

        orphaned_item_strategy_items = []
        if 'prune-dead-branches' in project_def:
            orphaned_item_strategy_items.append(
                ('prune-dead-branches', 'pruneDeadBranches',
                 False, [True, False]))

        orphaned_item_strategy_items.extend([
            ('days-to-keep', 'daysToKeep', -1),
            ('number-to-keep', 'numToKeep', -1),
        ])
        helpers.convert_mapping_to_xml(
            orphaned_item_strategy, project_def, orphaned_item_strategy_items)

        triggers = XML.SubElement(xml_parent, 'triggers')
        sub_trigger_items = []
        if 'timer-trigger' in project_def:
            timer_trigger = XML.SubElement(
                triggers, 'hudson.triggers.TimerTrigger')
            sub_trigger_items.append((timer_trigger, project_def,
                                      [('timer-trigger', 'spec', None)]))
        if 'periodic-folder-trigger' in project_def:
            periodic_folder_trigger = XML.SubElement(
                triggers,
                ('com.cloudbees.hudson.plugins.'
                 'folder.computed.PeriodicFolderTrigger'))
            periodic_folder_trigger.attrib['plugin'] = 'cloudbees-folder'
            sub_trigger_items.append(
                (periodic_folder_trigger, project_def,
                 [('periodic-folder-spec', 'spec', None),
                  ('periodic-folder-interval', 'interval', None)]))

        for parent, data, mapping in sub_trigger_items:
            helpers.convert_mapping_to_xml(parent, data, mapping)

        sources = XML.SubElement(xml_parent, 'sources')
        sources.attrib['class'] = ('jenkins.branch.MultiBranchProject'
                                   '$BranchSourceList')
        sources.attrib['plugin'] = 'branch-api'
        sources_data = XML.SubElement(sources, 'data')
        branch_source = XML.SubElement(
            sources_data, 'jenkins.branch.BranchSource')
        source = XML.SubElement(branch_source, 'source')
        XML.SubElement(source, 'id').text = str(uuid.uuid4())
        source_items = [
            ('includes', 'includes', '*'),
            ('excludes', 'excludes', ''),
        ]
        required_source_items = []
        scm_data = {}

        if 'scm' in project_def:
            scm = project_def['scm']
            if 'github' in scm:
                # See: https://github.com/jenkinsci/github-branch-source-plugin
                scm_data = scm['github']
                source.attrib['class'] = ('org.jenkinsci.plugins.'
                                          'github_branch_source.'
                                          'GitHubSCMSource')
                source.attrib['plugin'] = 'github-branch-source'
                source_items.extend([
                    ('api-uri', 'apiUri', None),
                    ('checkout-credentials-id',
                     'checkoutCredentialsId', None),
                ])
                required_source_items.extend([
                    ('scan-credentials-id', 'scanCredentialsId', None),
                    ('repo', 'repository', None),
                    ('repo-owner', 'repoOwner', None),
                ])
                # Deal with all these booleans in one swipe...
                #
                # Defaults are the same as what the jenkins source code of the
                # plugin sets them to.
                source_items.extend([
                    ('build-origin-branch', 'buildOriginBranch', True),
                    ('build-origin-branch-with-pr',
                     'buildOriginBranchWithPR', True),
                    ('build-origin-pr-merge', 'buildOriginPRMerge', False),
                    ('build-origin-pr-head', 'buildOriginPRHead', False),
                    ('build-fork-pr-head', 'buildForkPRHead', False),
                    ('build-fork-pr-merge', 'buildForkPRMerge', True),
                ])
            elif 'bitbucket' in scm:
                scm_data = scm['bitbucket']
                source.attrib['class'] = ('com.cloudbees.jenkins.plugins.'
                                          'bitbucket.BitbucketSCMSource')
                source.attrib['plugin'] = 'cloudbees-bitbucket-branch-source'
                source_items.extend([
                    ('checkout-credentials-id',
                     'checkoutCredentialsId', None),
                    ('bitbucket-server-url',
                     'bitbucketServerUrl', None),
                    ('ssh-port', 'sshPort', None),
                    ('repository-type', 'repositoryType', 'GIT')
                ])
                required_source_items.extend([
                    ('scan-credentials-id', 'credentialsId', 'SAME'),
                    ('repo', 'repository', None),
                    ('repo-owner', 'repoOwner', None),
                ])
                source_items.extend([
                    ('auto-register-webhook', 'autoRegisterHook', False),
                ])
            elif 'git' in scm:
                scm_data = scm['git']
                source.attrib['class'] = 'jenkins.plugins.git.GitSCMSource'
                source.attrib['plugin'] = 'git'
                required_source_items.extend([
                    ('url', 'remote', None),
                    ('credentials-id', 'credentialsId', None),
                ])
                source_items.extend([
                    ('api-uri', 'apiUri', None),
                    ('ignore-on-push-notifications',
                     'ignoreOnPushNotifications', True),
                ])
            else:
                raise InvalidAttributeError(
                    "Unknown/unsupported scm type specified")
        else:
            raise InvalidAttributeError(
                "Unknown/unsupported scm type specified")

        helpers.convert_mapping_to_xml(source, scm_data, source_items)
        helpers.convert_mapping_to_xml(
            source, scm_data, required_source_items, fail_required=True)

        owner = XML.SubElement(sources, 'owner')
        owner.attrib['class'] = ('org.jenkinsci.plugins.workflow.'
                                 'multibranch.WorkflowMultiBranchProject')
        owner.attrib['reference'] = '../..'

        factory = XML.SubElement(xml_parent, 'factory')
        factory.attrib['class'] = ('org.jenkinsci.plugins.workflow.'
                                   'multibranch.WorkflowBranchProjectFactory')
        factory_owner = XML.SubElement(factory, 'owner')
        factory_owner.attrib['class'] = ('org.jenkinsci.plugins.workflow.'
                                         'multibranch.'
                                         'WorkflowMultiBranchProject')
        factory_owner.attrib['reference'] = '../..'

        return xml_parent
