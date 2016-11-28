# -*- coding: utf-8 -*-
# Copyright (C) 2015 Joost van der Griendt <joostvdg@gmail.com>
# Copyright (C) 2018 Sorin Sbarnea <ssbarnea@users.noreply.github.com>
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
The Multibranch Pipeline project module handles creating Jenkins workflow
projects.
You may specify ``multibranch`` in the ``project-type`` attribute of
the :ref:`Job` definition.

Multibranch Pipeline implementantion in JJB is marked as **experimental**
which means that there is no guarantee that its behavior (or configuration)
will not change, even between minor releases.

Plugins required:
    * :jenkins-wiki:`Workflow Plugin <Workflow+Plugin>`.
    * :jenkins-wiki:`Pipeline Multibranch Defaults Plugin
      <Pipeline+Multibranch+Defaults+Plugin>` (optional for adding
      ``multibranch-defaults`` project type which allows loading
      pipeline code (Jenkinsfile) from Jenkins master instead of repository.
      Use of this project-type is optional as the same functionality can
      be obtained just by configuring ``multibranch`` one once the plugin
      is installed.
    * :jenkins-wiki:`Gerrit Code Review Plugin <Gerrit+Code+Review+Plugin>`
      (optional for enabling Gerrit SCM support)
    * :jenkins-wiki:`Git Plugin <Git+Plugin>` (optional
      for enabling Git SCM support)
    * :jenkins-wiki:`GitHub Branch Source Plugin <GitHub+Branch+Source+Plugin>`
      (optional for enabling Git SCM support)
    * :jenkins-wiki:`Bitbucket Branch Source Plugin
      <Bitbucket+Branch+Source+Plugin>` (optional for enabling Bitbucket
      SCM support)

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

Job examples:

.. literalinclude::
   /../../tests/modules/fixtures/project_multibranch_git_min.yaml

.. literalinclude::
   /../../tests/modules/fixtures/project_multibranch_github_min.yaml

.. literalinclude::
   /../../tests/modules/fixtures/project_multibranch_gerrit_min.yaml

.. literalinclude::
   /../../tests/modules/fixtures/project_multibranch_bitbucket_min.yaml

.. literalinclude::
   /../../tests/modules/fixtures/project_multibranch_defaults.yaml

.. literalinclude::
   /../../tests/modules/fixtures/project_multibranch_multi_scm_full.yaml

"""
import collections
import logging
import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers
import uuid
import six

from jenkins_jobs.errors import InvalidAttributeError

logger = logging.getLogger(str(__name__))


class WorkflowMultiBranch(jenkins_jobs.modules.base.Base):
    sequence = 0
    multibranch_path = 'org.jenkinsci.plugins.workflow.multibranch'
    jenkins_class = ''.join([multibranch_path, '.WorkflowMultiBranchProject'])
    jenkins_factory_class = ''.join(
        [multibranch_path, '.WorkflowBranchProjectFactory'])

    def root_xml(self, data):
        xml_parent = XML.Element(self.jenkins_class)
        xml_parent.attrib['plugin'] = 'workflow-multibranch'
        XML.SubElement(xml_parent, 'properties')

        # Views
        views = XML.SubElement(xml_parent, 'views')
        all_view = XML.SubElement(views, 'hudson.model.AllView')
        all_view_mapping = [
            ('', 'name', 'All'),
            ('', 'filterExecutors', False),
            ('', 'filterQueue', False),
        ]
        helpers.convert_mapping_to_xml(
            all_view, {}, all_view_mapping, fail_required=True)

        XML.SubElement(all_view, 'properties', {
            'class': 'hudson.model.View$PropertyList'
        })

        XML.SubElement(all_view, 'owner', {
            'class': self.jenkins_class,
            'reference': '../../..'
        })

        XML.SubElement(xml_parent, 'viewsTabBar', {
            'class': 'hudson.views.DefaultViewsTabBar'
        })

        # Folder Views
        folderViews = XML.SubElement(xml_parent, 'folderViews', {
            'class': 'jenkins.branch.MultiBranchProjectViewHolder',
            'plugin': 'branch-api',
        })

        XML.SubElement(folderViews, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..'
        })

        # Health Metrics
        hm = XML.SubElement(xml_parent, 'healthMetrics')
        hm_path = ('com.cloudbees.hudson.plugins.folder.health'
                   '.WorstChildHealthMetric')
        hm_plugin = XML.SubElement(hm, hm_path, {
            'plugin': 'cloudbees-folder',
        })
        XML.SubElement(hm_plugin, 'nonRecursive').text = 'false'

        # Icon
        icon = XML.SubElement(xml_parent, 'icon', {
            'class': 'jenkins.branch.MetadataActionFolderIcon',
            'plugin': 'branch-api',
        })
        XML.SubElement(icon, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..'
        })

        # Orphan Item Strategy
        ois_default_strategy = ('com.cloudbees.hudson.plugins.'
            'folder.computed.DefaultOrphanedItemStrategy')
        ois = XML.SubElement(
            xml_parent, 'orphanedItemStrategy', {
                'class': ois_default_strategy,
                'plugin': 'cloudbees-folder',
            }
        )

        ois_mapping = [
            ('prune-dead-branches', 'pruneDeadBranches', True, [True, False]),
            ('days-to-keep', 'daysToKeep', -1),
            ('number-to-keep', 'numToKeep', -1),
        ]
        helpers.convert_mapping_to_xml(ois, data, ois_mapping)

        # Periodic Folder Trigger
        triggers = XML.SubElement(xml_parent, 'triggers')

        # Valid options for the periodic trigger interval.
        pft_map = collections.OrderedDict([
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
            ("4w", ("H H * * *", '2419200000')),
        ])

        pft_val = data.get('periodic-folder-trigger')
        if pft_val:
            if not pft_map.get(pft_val):
                raise InvalidAttributeError(
                    'periodic-folder-trigger',
                    pft_val,
                    pft_map.keys())

            pft_path = (
                'com.cloudbees.hudson.plugins.folder.computed.'
                'PeriodicFolderTrigger')
            pft = XML.SubElement(triggers, pft_path, {
                'plugin': 'cloudbees-folder'
            })
            XML.SubElement(pft, 'spec').text = pft_map[pft_val][0]
            XML.SubElement(pft, 'interval').text = pft_map[pft_val][1]

        # Sources
        sources = XML.SubElement(xml_parent, 'sources', {
            'class': 'jenkins.branch.MultiBranchProject$BranchSourceList',
            'plugin': 'branch-api',
        })
        sources_data = XML.SubElement(sources, 'data')
        XML.SubElement(sources, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..',
        })

        valid_scm = [
            'bitbucket',
            'gerrit',
            'git',
            'github',
        ]
        for scm_data in data.get('scm', None):
            for scm in scm_data:
                bs = XML.SubElement(
                    sources_data, 'jenkins.branch.BranchSource')

                if scm == 'bitbucket':
                    bitbucket_scm(bs, scm_data[scm])

                elif scm == 'gerrit':
                    gerrit_scm(bs, scm_data[scm])

                elif scm == 'git':
                    git_scm(bs, scm_data[scm])

                elif scm == 'github':
                    github_scm(bs, scm_data[scm])

                else:
                    raise InvalidAttributeError('scm', scm_data, valid_scm)

        # Factory
        factory = XML.SubElement(xml_parent, 'factory', {
            'class': self.jenkins_factory_class,
        })
        XML.SubElement(factory, 'owner', {
            'class': self.jenkins_class,
            'reference': '../..'
        })
        XML.SubElement(factory, 'scriptPath').text = 'Jenkinsfile'

        return xml_parent


class WorkflowMultiBranchDefaults(WorkflowMultiBranch):
        jenkins_class = (
            'org.jenkinsci.plugins.pipeline.multibranch'
            '.defaults.PipelineMultiBranchDefaultsProject')
        jenkins_factory_class = (
            'org.jenkinsci.plugins.pipeline.multibranch'
            '.defaults.PipelineBranchDefaultsProjectFactory')


def bitbucket_scm(xml_parent, data):
    """Configure BitBucket scm

    Requires :jenkins-wiki:`Bitbucket Branch Source Plugin
    <Bitbucket+Branch+Source+Plugin>`.
    """
    source = XML.SubElement(xml_parent, 'source', {
        'class': 'com.cloudbees.jenkins.plugins.bitbucket.BitbucketSCMSource',
        'plugin': 'cloudbees-bitbucket-branch-source',
    })
    source_mapping = [
        ('', 'id', str(uuid.uuid4())),
        ('includes', 'includes', '*'),
        ('excludes', 'excludes', ''),
        ('scan-credentials-id', 'credentialsId', None),
        ('repo', 'repository', None),
        ('repo-owner', 'repoOwner', None),
        ('repository-type', 'repositoryType', 'GIT'),
        ('auto-register-webhook', 'autoRegisterHook', False),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    source_mapping_optional = [
        ('checkout-credentials-id', 'checkoutCredentialsId', None),
        ('bitbucket-server-url', 'bitbucketServerUrl', None),
        ('ssh-port', 'sshPort', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping_optional, fail_required=False)

    XML.SubElement(source, 'traits')


def gerrit_scm(xml_parent, data):
    """Configure Gerrit SCM

    Requires :jenkins-wiki:`Gerrit Code Review Plugin
    <Gerrit+Code+Review+Plugin>`.
    """
    source = XML.SubElement(xml_parent, 'source', {
        'class': 'jenkins.plugins.gerrit.GerritSCMSource',
        'plugin': 'gerrit',
    })
    source_mapping = [
        ('', 'id', str(uuid.uuid4())),
        ('url', 'remote', None),
        ('includes', 'includes', '*'),
        ('excludes', 'excludes', ''),
        ('ignore-on-push-notifications', 'ignoreOnPushNotifications', True),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    source_mapping_optional = [
        ('api-uri', 'apiUri', None),
        ('credentials-id', 'credentialsId', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping_optional, fail_required=False)

    # Traits
    traits = XML.SubElement(source, 'traits')
    XML.SubElement(traits,
        'jenkins.plugins.gerrit.traits.ChangeDiscoveryTrait')

    # Refspec Trait
    refspec_trait = XML.SubElement(
        traits, 'jenkins.plugins.git.traits.RefSpecsSCMSourceTrait', {
            'plugin': 'git',
        }
    )
    templates = XML.SubElement(refspec_trait, 'templates')
    refspecs = data.get('refspecs', [
        '+refs/changes/*:refs/remotes/@{remote}/*',
        '+refs/heads/*:refs/remotes/@{remote}/*',
    ])
    # convert single string to list
    if isinstance(refspecs, six.string_types):
        refspecs = [refspecs]
    for x in refspecs:
        e = XML.SubElement(
            templates, ('jenkins.plugins.git.traits'
            '.RefSpecsSCMSourceTrait_-RefSpecTemplate'))
        XML.SubElement(e, 'value').text = x


def git_scm(xml_parent, data):
    """Configure Git SCM

    Requires :jenkins-wiki:`Git Plugin <Git+Plugin>`.
    """
    source = XML.SubElement(xml_parent, 'source', {
        'class': 'jenkins.plugins.git.GitSCMSource',
        'plugin': 'git',
    })
    source_mapping = [
        ('', 'id', str(uuid.uuid4())),
        ('url', 'remote', None),
        ('includes', 'includes', '*'),
        ('excludes', 'excludes', ''),
        ('ignore-on-push-notifications', 'ignoreOnPushNotifications', True),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    source_mapping_optional = [
        ('api-uri', 'apiUri', None),
        ('credentials-id', 'credentialsId', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping_optional, fail_required=False)

    traits = XML.SubElement(source, 'traits')
    XML.SubElement(traits, 'jenkins.plugins.git.traits.BranchDiscoveryTrait')


def github_scm(xml_parent, data):
    """Configure GitHub SCM

    Requires :jenkins-wiki:`GitHub Branch Source Plugin
    <GitHub+Branch+Source+Plugin>`.

    https://github.com/jenkinsci/github-branch-source-plugin
    """
    github_path = 'org.jenkinsci.plugins.github_branch_source'
    github_path_dscore = 'org.jenkinsci.plugins.github__branch__source'

    source = XML.SubElement(xml_parent, 'source', {
        'class': ''.join([github_path, '.GitHubSCMSource']),
        'plugin': 'github-branch-source',
    })
    source_mapping = [
        ('', 'id', str(uuid.uuid4())),
        ('includes', 'includes', '*'),
        ('excludes', 'excludes', ''),
        ('build-origin-branch', 'buildOriginBranch', True),
        ('build-origin-branch-with-pr', 'buildOriginBranchWithPR', True),
        ('build-origin-pr-merge', 'buildOriginPRMerge', False),
        ('build-origin-pr-head', 'buildOriginPRHead', False),
        ('build-fork-pr-head', 'buildForkPRHead', False),
        ('build-fork-pr-merge', 'buildForkPRMerge', True),
        ('scan-credentials-id', 'scanCredentialsId', None),
        ('repo', 'repository', None),
        ('repo-owner', 'repoOwner', None),
    ]
    helpers.convert_mapping_to_xml(
        source, data, source_mapping, fail_required=True)

    traits = XML.SubElement(source, 'traits')

    if data.get('branch-discovery', None):
        bd = XML.SubElement(traits, ''.join([
            github_path_dscore, '.BranchDiscoveryTrait']))
        branch_disc_strategy = {
            'no-pr': '1',
            'only-pr': '2',
            'all': '3',
        }
        XML.SubElement(bd, 'strategyId').text = (
            branch_disc_strategy[data['branch-discovery']])

    if data.get('discover-pr-forks-strategy', None):
        dprfs = XML.SubElement(
            traits, ''.join([
                github_path_dscore, '.ForkPullRequestDiscoveryTrait'
            ])
        )
        strategy = {
            'merge-current': '1',
            'current': '2',
            'both': '3',
        }
        XML.SubElement(dprfs, 'strategyId').text = (
            strategy[data['discover-pr-forks-strategy']])

        trust = data.get('discover-pr-forks-trust', 'contributors')
        trust_map = {
            'contributors': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustContributors']),
            'everyone': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustEveryone']),
            'permission': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustPermission']),
            'nobody': ''.join([
                github_path,
                '.ForkPullRequestDiscoveryTrait$TrustNobody']),
        }
        XML.SubElement(dprfs, 'trust').attrib['class'] = trust_map[trust]

    if data.get('discover-pr-origin', None):
        dpro = XML.SubElement(traits, ''.join([
            github_path_dscore,
            '.OriginPullRequestDiscoveryTrait'
        ]))
        dpro_strategy = {
            'merge-current': '1',
            'current': '2',
            'both': '3',
        }
        XML.SubElement(dpro, 'strategyId').text = (
            dpro_strategy[data['discover-pr-origin']])
