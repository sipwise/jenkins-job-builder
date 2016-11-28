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
You may specify ``multibranch`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Multibranch Pipeline implementantion in JJB is marked as **experimental**
which means that there is no guarantee that its behavior (or configuration)
will not change, even between minor releases.

Plugins required:
    * :jenkins-wiki:`Workflow Plugin <Workflow+Plugin>`.
    * :jenkins-wiki:`Gerrit Plugin <Gerrit+Code+Review+Plugin>` (optional
      for enabling Gerrit SCM support)

:Job Parameters:

    * **scm** (`list`): The SCM definition.

        * **git** (`str`): Use this as sub-structure of scm when using git.
            * **url** (`str`): The git url.
            * **credentials-id** (`str`): The credentialsId to use to connect
              to the GIT URL.
            * **includes** (`str`): Which branches should be
              included. (defaults to \*, all)  (optional)
            * **excludes** (`str`): Which branches should be
              excluded. (defaults to empty, none)  (optional)
            * **ignore-on-push-notifications** (`bool`): If a job should
              not trigger upon push notifications. (defaults to
              false) (optional)
        * **gerrit** (`str`): Gerrit SCM.
            * **url** (`str`): The git url.
            * **credentials-id** (`str`): The credentialsId to use to connect
              to the GIT URL.
            * **ignore-on-push-notifications** (`bool`): If a job should
              not trigger upon push notifications. (defaults to
              false) (optional)
            * **refspecs** (`str` or `list(str)`): Which refspecs to look for.
              Defaults to ``['+refs/changes/*:refs/remotes/@{remote}/*',
              '+refs/heads/*:refs/remotes/@{remote}/*']``

        * **github** (`str`): Use with github SCM plugin.
            * **repo** (`str`): The github repo.
            * **repo-owner** (`str`): The github repo owner.
            * **scan-credentials-id** (`str`): The credentialsId to use
              to scan github.
            * **checkout-credentials-id** (`str`): The credentialsId to use
              to checkout from github.  (defaults to same as
              scan-credentials-id) (optional)
            * **includes** (`str`): Which branches should be included.
              (defaults to \*, all)
            * **excludes** (`str`): (optional) be excluded. (defaults
              to empty, none)  (optional)
            * **api-uri** (`str`): The github api uri (for
              hosted/on-site github).  (optional)
            * **build-origin-branch** (`bool`) Build origin branches.
              (defaults to true) (optional)
            * **build-origin-branch-with-pr** (`bool`) Build origin
              branches also filed as PRs.  (defaults to true) (optional)
            * **build-origin-pr-merge** (`bool`) Build origin PRs (merged with
              base branch).  (defaults to false) (optional)
            * **build-origin-pr-head** (`bool`) Build origin PRs (unmerged
              head).  (defaults to false) (optional)
            * **build-fork-pr-merge** (`bool`) Build fork PRs (merged
              with base branch).  (defaults to true) (optional)
            * **build-fork-pr-head** (`bool`) Build fork
              PRs (unmerged head).  (defaults to false) (optional)
            * **branch-discovery** (`str`): no-pr, only-pr, all.  (defaults
              to undefined)
            * **discover-pr-forks-strategy** (`str`): merge-current, current,
              both.  (defaults to undefined)
            * **discover-pr-forks-trust** (`str`): contributors, everyone,
              permission or nobody.  (defaults to contributors)
            * **discover-pr-origin** (`str`): merge-current, current,
              both.  (defaults to undefined)

        * **bitbucket** (`str`): Use this with bitbucket SCM plugin.
            * **repo** (`str`): The repo.
            * **repo-owner** (`str`): Bitbucket project/repo owner.
            * **scan-credentials-id** (`str`): The credentialsId to use
              to scan github. (defaults to 'SAME')
            * **checkout-credentials-id** (`str`): The credentialsId to use
              to checkout from bitbucket.  (defaults to empty, none)
              (optional)
            * **includes** (`str`): Which branches should be
              included. (defaults to \*, all)  (optional) be excluded.
              (defaults to empty, none)  (optional)
            * **bitbucket-server-url** (`str`) Bitbucket server URL, to be set
              when used with Bitbucket Server. (defaults to empty, none)
              (optional)
            * **auto-register-webhook** (`bool`) Register webhook in Bitbucket.
              (defaults to false) (optional)
            * **ssh-port** (`int`) Bitbucket ssh port. (defaults to empty,
              none)
              (optional)
            * **repository-type** (`str`) Bitbucket repo type. (defaults to
              'GIT') (optional)

    * **periodic-folder-trigger** (`str`): How often to scan for new branches
      or pull/change requests. Valid values: 1m, 2m, 5m, 10m, 15m, 20m, 25m,
      30m, 1h, 2h, 4h, 8h, 12h, 1d, 2d, 1w, 2w, 4w. Default: None.
    * **prune-dead-branches** (`bool`): If dead branches upon check should
      result in their job being dropped. (defaults to true) (optional)
    * **number-to-keep** (`int`): How many builds should be
      kept. (defaults to -1, all) (optional)
    * **days-to-keep** (`int`): For how many days should a build
      be kept. (defaults to -1, forever) (optional)

Job with inline script example:

.. literalinclude::
   /../../tests/modules/fixtures/project_pipeline_multibranch_template001.yaml

"""
import collections
import logging
import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import uuid
import six

from jenkins_jobs.errors import InvalidAttributeError
from jenkins_jobs.modules import helpers

logger = logging.getLogger(str(__name__))


class WorkflowMultiBranch(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):

        project_def = data

        xml_parent = XML.Element(
            ('org.jenkinsci.plugins.workflow.'
             'multibranch.WorkflowMultiBranchProject'))
        xml_parent.attrib['plugin'] = 'workflow-multibranch'

        XML.SubElement(xml_parent, 'properties')

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

        folderViews = XML.SubElement(xml_parent, 'folderViews')
        folderViews.attrib['class'] = 'jenkins.branch.MultiBranchProjectViewHolder'  # noqa
        folderViews.attrib['plugin'] = 'branch-api'
        folderViews_owner = XML.SubElement(folderViews, 'owner')
        folderViews_owner.attrib['class'] = 'org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject'  # noqa
        folderViews_owner.attrib['reference'] = '../..'

        health_metrics = XML.SubElement(xml_parent, 'healthMetrics')
        health_metrics_plugin = XML.SubElement(
            health_metrics,
            ('com.cloudbees.hudson.plugins.'
             'folder.health.WorstChildHealthMetric'))
        health_metrics_plugin.attrib['plugin'] = 'cloudbees-folder'
        XML.SubElement(health_metrics_plugin, 'nonRecursive').text = 'false'

        icon = XML.SubElement(xml_parent, 'icon')
        icon.attrib['class'] = 'jenkins.branch.MetadataActionFolderIcon'

        # icon.attrib['class'] = ('com.cloudbees.hudson.plugins'
        #                         '.folder.icons.StockFolderIcon')
        icon.attrib['plugin'] = 'branch-api'
        icon_owner = XML.SubElement(icon, 'owner')
        icon_owner.attrib['class'] = "org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject"  # noqa
        icon_owner.attrib['reference'] = '../..'

        orphaned_item_strategy = XML.SubElement(
            xml_parent, 'orphanedItemStrategy')
        orphaned_item_strategy.attrib['class'] = (
            'com.cloudbees.hudson.plugins.folder.computed.'
            'DefaultOrphanedItemStrategy')
        orphaned_item_strategy.attrib['plugin'] = 'cloudbees-folder'

        orphaned_item_strategy_items = []
        orphaned_item_strategy_items.append(
            ('prune-dead-branches', 'pruneDeadBranches',
             True, [True, False]))

        orphaned_item_strategy_items.extend([
            ('days-to-keep', 'daysToKeep', -1),
            ('number-to-keep', 'numToKeep', -1),
        ])
        helpers.convert_mapping_to_xml(
            orphaned_item_strategy, project_def, orphaned_item_strategy_items)

        triggers = XML.SubElement(xml_parent, 'triggers')
        sub_trigger_items = []

        periodic_trigger_map = collections.OrderedDict([
            ("1m", ("* * * * *", '60000')),
            ("2m", ("*/2 * * * *", '120000')),
            ("5m", ("*/5 * * * *", '300000')),
            ("10m", ("H/6 * * * *", '600000')),
            ("15m", ("H/6 * * * *", '900000')),
            ("20m", ("H/3 * * * *", '1200000')),
            ("25m", ("H/3 * * * *", '1500000')),
            ("30m", ("H/2 * * * *", '1800000')),
            ("1h", ("H * * * *", '3600000')),
            ("2h", ("H * * * *", '7200000')),
            ("4h", ("H * * * *", '14400000')),
            ("8h", ("H * * * *", '28800000')),
            ("12h", ("H H * * *", '43200000')),
            ("1d", ("H H * * *", '86400000')),
            ("2d", ("H H * * *", '172800000')),
            ("1w", ("H H * * *", '604800000')),
            ("2w", ("H H * * *", '1209600000')),
            ("4w", ("H H * * *", '2419200000'))])
        periodic_folder_trigger_val = \
            project_def.get('periodic-folder-trigger')
        if periodic_folder_trigger_val:
            if not periodic_trigger_map.get(periodic_folder_trigger_val):
                raise InvalidAttributeError(
                    'periodic-folder-trigger',
                    periodic_folder_trigger_val,
                    periodic_trigger_map.keys())

            periodic_folder_trigger = XML.SubElement(
                triggers,
                ('com.cloudbees.hudson.plugins.'
                 'folder.computed.PeriodicFolderTrigger'))
            periodic_folder_trigger.attrib['plugin'] = 'cloudbees-folder'

            XML.SubElement(periodic_folder_trigger, 'spec').text = \
                periodic_trigger_map[periodic_folder_trigger_val][0]
            XML.SubElement(periodic_folder_trigger, 'interval').text = \
                periodic_trigger_map[periodic_folder_trigger_val][1]

        sources = XML.SubElement(xml_parent, 'sources')
        sources.attrib['class'] = ('jenkins.branch.MultiBranchProject'
                                   '$BranchSourceList')
        sources.attrib['plugin'] = 'branch-api'
        sources_data = XML.SubElement(sources, 'data')
        owner = XML.SubElement(sources, 'owner')
        owner.attrib['class'] = ('org.jenkinsci.plugins.workflow.'
                                 'multibranch.WorkflowMultiBranchProject')
        owner.attrib['reference'] = '../..'

        for parent, data, mapping in sub_trigger_items:
            helpers.convert_mapping_to_xml(parent, data, mapping)

        if 'scm' not in project_def:
            raise InvalidAttributeError(
                "Unknown/unsupported scm type specified")

        for scm in project_def['scm']:

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
            traits = XML.SubElement(source, 'traits')

            if 'github' in scm:
                # https://github.com/jenkinsci/github-branch-source-plugin
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
                # Defaults are the same as what the jenkins source code of
                # the plugin sets them to.
                source_items.extend([
                    ('build-origin-branch', 'buildOriginBranch', True),
                    ('build-origin-branch-with-pr',
                     'buildOriginBranchWithPR', True),
                    ('build-origin-pr-merge', 'buildOriginPRMerge', False),
                    ('build-origin-pr-head', 'buildOriginPRHead', False),
                    ('build-fork-pr-head', 'buildForkPRHead', False),
                    ('build-fork-pr-merge', 'buildForkPRMerge', True),
                ])

                if scm_data.get('branch-discovery', None):
                    e = XML.SubElement(traits, "org.jenkinsci.plugins.github__branch__source.BranchDiscoveryTrait")  # noqa
                    branch_disc_strategy = {'no-pr': '1',
                                            'only-pr': '2',
                                            'all': '3'}
                    XML.SubElement(e, 'strategyId').text =\
                        branch_disc_strategy[scm_data['branch-discovery']]

                if scm_data.get('discover-pr-forks-strategy', None):
                    e = XML.SubElement(traits,
                                       "org.jenkinsci.plugins.github__branch__source.ForkPullRequestDiscoveryTrait")  # noqa
                    strategy = {'merge-current': '1',
                                'current': '2',
                                'both': '3'}
                    XML.SubElement(e, 'strategyId').text = \
                        strategy[scm_data['discover-pr-forks-strategy']]

                    trust = scm_data.get('discover-pr-forks-trust',
                                         'contributors')
                    trust_map = {
                        'contributors': 'org.jenkinsci.plugins.github_branch_source.ForkPullRequestDiscoveryTrait$TrustContributors',  # noqa
                        'everyone': 'org.jenkinsci.plugins.github_branch_source.ForkPullRequestDiscoveryTrait$TrustEveryone',  # noqa
                        'permission': 'org.jenkinsci.plugins.github_branch_source.ForkPullRequestDiscoveryTrait$TrustPermission',  # noqa
                        'nobody': 'org.jenkinsci.plugins.github_branch_source.ForkPullRequestDiscoveryTrait$TrustNobody'  # noqa
                    }
                    XML.SubElement(e, 'trust').attrib['class'] = \
                        trust_map[trust]

                if scm_data.get('discover-pr-origin', None):
                    strategy = {'merge-current': '1',
                                'current': '2',
                                'both': '3'}
                    e = XML.SubElement(traits,
                                       "org.jenkinsci.plugins.github__branch__source.OriginPullRequestDiscoveryTrait")  # noqa
                    XML.SubElement(e, 'strategyId').text = \
                        strategy[scm_data['discover-pr-origin']]

            elif 'bitbucket' in scm:
                scm_data = scm['bitbucket']
                source.attrib['class'] = ('com.cloudbees.jenkins.plugins.'
                                          'bitbucket.BitbucketSCMSource')
                source.attrib['plugin'] = \
                    'cloudbees-bitbucket-branch-source'
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
                ])
                source_items.extend([
                    ('api-uri', 'apiUri', None),
                    ('ignore-on-push-notifications',
                     'ignoreOnPushNotifications', True),
                    ('credentials-id', 'credentialsId', None),
                ])
            elif 'gerrit' in scm:
                scm_data = scm['gerrit']
                source.attrib['class'] = \
                    'jenkins.plugins.gerrit.GerritSCMSource'
                source.attrib['plugin'] = 'gerrit'
                required_source_items.extend([
                    ('url', 'remote', None),
                ])
                source_items.extend([
                    ('api-uri', 'apiUri', None),
                    ('ignore-on-push-notifications',
                     'ignoreOnPushNotifications', True),
                    ('credentials-id', 'credentialsId', None),
                ])

                XML.SubElement(traits, "jenkins.plugins.gerrit.traits.ChangeDiscoveryTrait")  # noqa
                RefSpecsSCMSourceTrait =\
                    XML.SubElement(traits, "jenkins.plugins.git.traits.RefSpecsSCMSourceTrait")  # noqa
                RefSpecsSCMSourceTrait.attrib['plugin'] = 'git'
                templates = XML.SubElement(RefSpecsSCMSourceTrait, 'templates')  # noqa
                refspecs = scm_data.get('refspecs', [
                    '+refs/changes/*:refs/remotes/@{remote}/*',
                    '+refs/heads/*:refs/remotes/@{remote}/*'])
                # convert single string to list
                if isinstance(refspecs, six.string_types):
                    refspecs = [refspecs]
                for x in refspecs:
                    e = XML.SubElement(templates, 'jenkins.plugins.git.traits.RefSpecsSCMSourceTrait_-RefSpecTemplate')  # noqa
                    XML.SubElement(e, 'value').text = x
            else:
                raise InvalidAttributeError(
                    "Unknown/unsupported scm type specified")

            logger.info(scm_data)

            helpers.convert_mapping_to_xml(source, scm_data, source_items)
            helpers.convert_mapping_to_xml(
                source,
                scm_data,
                required_source_items,
                fail_required=True)

        factory = XML.SubElement(xml_parent, 'factory')
        factory.attrib['class'] = ('org.jenkinsci.plugins.workflow.'
                                   'multibranch.WorkflowBranchProjectFactory')
        factory_owner = XML.SubElement(factory, 'owner')
        factory_owner.attrib['class'] = ('org.jenkinsci.plugins.workflow.'
                                         'multibranch.'
                                         'WorkflowMultiBranchProject')
        factory_owner.attrib['reference'] = '../..'

        XML.SubElement(factory, 'scriptPath').text = 'Jenkinsfile'

        return xml_parent
