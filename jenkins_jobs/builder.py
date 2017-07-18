#!/usr/bin/env python
# Copyright (C) 2012 OpenStack, LLC.
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

# Manage jobs in Jenkins server

import errno
import hashlib
import io
import logging
import operator
import os
from pprint import pformat
import re
import time
import xml.etree.ElementTree as XML

import jenkins

from jenkins_jobs.cache import JobCache
from jenkins_jobs.constants import MAGIC_MANAGE_STRING
from jenkins_jobs.parallel import concurrent
from jenkins_jobs import utils

__all__ = [
    "JenkinsManager"
]

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = object()


class JenkinsManager(object):

    def __init__(self, jjb_config):
        url = jjb_config.jenkins['url']
        user = jjb_config.jenkins['user']
        password = jjb_config.jenkins['password']
        timeout = jjb_config.jenkins['timeout']

        if timeout != _DEFAULT_TIMEOUT:
            self.jenkins = jenkins.Jenkins(url, user, password, timeout)
        else:
            self.jenkins = jenkins.Jenkins(url, user, password)

        self.cache = JobCache(jjb_config.jenkins['url'],
                              flush=jjb_config.builder['flush_cache'])

        self._plugins_list = jjb_config.builder['plugins_info']
        self._jobs = None
        self._job_list = None
        self._promoted_builds = None
        self._promoted_build_list = None
        self._views = None
        self._view_list = None
        self._jjb_config = jjb_config

    @property
    def jobs(self):
        if self._jobs is None:
            # populate jobs
            self._jobs = self.jenkins.get_jobs()

        return self._jobs

    @property
    def job_list(self):
        if self._job_list is None:
            self._job_list = set(job['name'] for job in self.jobs)
        return self._job_list

    def update_job(self, job_name, xml):
        if self.is_job(job_name):
            logger.info("Reconfiguring jenkins job {0}".format(job_name))
            self.jenkins.reconfig_job(job_name, xml)
        else:
            logger.info("Creating jenkins job {0}".format(job_name))
            self.jenkins.create_job(job_name, xml)

    def is_job(self, job_name):
        # first use cache
        if job_name in self.job_list:
            return True

        # if not exists, use jenkins
        return self.jenkins.job_exists(job_name)

    def get_job_md5(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        return hashlib.md5(xml.encode('utf-8')).hexdigest()

    def delete_job(self, job_name):
        if self.is_job(job_name):
            logger.info("Deleting jenkins job {0}".format(job_name))
            self.jenkins.delete_job(job_name)

    def get_plugins_info(self):
        """ Return a list of plugin_info dicts, one for each plugin on the
        Jenkins instance.
        """
        try:
            plugins_list = self.jenkins.get_plugins().values()

        except jenkins.JenkinsException as e:
            if re.search("Connection refused", str(e)):
                logger.warning(
                    "Unable to retrieve Jenkins Plugin Info from {0},"
                    " using default empty plugins info list.".format(
                        self.jenkins.server))
                plugins_list = [{'shortName': '',
                                 'version': '',
                                 'longName': ''}]
            else:
                raise e
        logger.debug("Jenkins Plugin Info {0}".format(pformat(plugins_list)))

        return plugins_list

    def get_jobs(self, cache=True):
        if not cache:
            self._jobs = None
            self._job_list = None
        return self.jobs

    def is_managed(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        try:
            out = XML.fromstring(xml)
            description = out.find(".//description").text
            return description.endswith(MAGIC_MANAGE_STRING)
        except (TypeError, AttributeError):
            pass
        return False

    @property
    def plugins_list(self):
        if self._plugins_list is None:
            self._plugins_list = self.get_plugins_info()
        return self._plugins_list

    def delete_old_managed(self, keep=None):
        jobs = self.get_jobs()
        deleted_jobs = 0
        if keep is None:
            keep = []
        for job in jobs:
            if job['name'] not in keep:
                if self.is_managed(job['name']):
                    logger.info("Removing obsolete jenkins job {0}"
                                .format(job['name']))
                    self.delete_job(job['name'])
                    deleted_jobs += 1
                else:
                    logger.info("Not deleting unmanaged jenkins job %s",
                                job['name'])
            else:
                logger.debug("Keeping job %s", job['name'])
        return deleted_jobs

    def delete_jobs(self, jobs):
        if jobs is not None:
            logger.info("Removing jenkins job(s): %s" % ", ".join(jobs))
        for job in jobs:
            try:
                promoted_builds = self.jenkins.get_promotions(job)
            except jenkins.NotFoundException:
                promoted_builds = []

            self.delete_job(job)
            if(self.cache.is_cached(job)):
                self.cache.set(job, '')

            for pb in promoted_builds:
                pb_name = self.safe_promoted_build_name(pb['name'], job)
                if self.cache.is_cached(pb_name):
                    self.cache.set(pb_name, '')

        self.cache.save()

    def delete_all_jobs(self):
        jobs = self.get_jobs()
        logger.info("Number of jobs to delete:  %d", len(jobs))
        script = ('for(job in jenkins.model.Jenkins.theInstance.getAllItems())'
                  '       { job.delete(); }')
        self.jenkins.run_script(script)
        # Need to clear the JJB cache after deletion
        self.cache.clear()

    def changed(self, job):
        md5 = job.md5()

        changed = (self._jjb_config.builder['ignore_cache'] or
                   self.cache.has_changed(job.name, md5))
        if not changed:
            logger.debug("'{0}' has not changed".format(job.name))
        return changed

    def update_jobs(self, xml_jobs, output=None, n_workers=None,
                    config_xml=False):
        orig = time.time()

        logger.info("Number of jobs generated:  %d", len(xml_jobs))
        xml_jobs.sort(key=operator.attrgetter('name'))

        if (output and not hasattr(output, 'write') and
                not os.path.isdir(output)):
            logger.info("Creating directory %s" % output)
            try:
                os.makedirs(output)
            except OSError:
                if not os.path.isdir(output):
                    raise

        if output:
            # ensure only wrapped once
            if hasattr(output, 'write'):
                output = utils.wrap_stream(output)

            for job in xml_jobs:
                if hasattr(output, 'write'):
                    # `output` is a file-like object
                    logger.info("Job name:  %s", job.name)
                    logger.debug("Writing XML to '{0}'".format(output))
                    try:
                        output.write(job.output())
                    except IOError as exc:
                        if exc.errno == errno.EPIPE:
                            # EPIPE could happen if piping output to something
                            # that doesn't read the whole input (e.g.: the UNIX
                            # `head` command)
                            return
                        raise
                    continue

                if config_xml:
                    output_dir = os.path.join(output, job.name)
                    logger.info("Creating directory %s" % output_dir)
                    try:
                        os.makedirs(output_dir)
                    except OSError:
                        if not os.path.isdir(output_dir):
                            raise
                    output_fn = os.path.join(output_dir, 'config.xml')
                else:
                    output_fn = os.path.join(output, job.name)
                logger.debug("Writing XML to '{0}'".format(output_fn))
                with io.open(output_fn, 'w', encoding='utf-8') as f:
                    f.write(job.output().decode('utf-8'))
            return xml_jobs, len(xml_jobs)

        # Filter out the jobs that did not change
        logging.debug('Filtering %d jobs for changed jobs',
                      len(xml_jobs))
        step = time.time()
        jobs = [job for job in xml_jobs
                if self.changed(job)]
        logging.debug("Filtered for changed jobs in %ss",
                      (time.time() - step))

        if not jobs:
            return [], 0

        # Update the jobs
        logging.debug('Updating jobs')
        step = time.time()
        p_params = [{'job': job} for job in jobs]
        results = self.parallel_update_job(
            n_workers=n_workers,
            concurrent=p_params)
        logging.debug("Parsing results")
        # generalize the result parsing, as a concurrent job always returns a
        # list
        if len(p_params) in (1, 0):
            results = [results]
        for result in results:
            if isinstance(result, Exception):
                raise result
            else:
                # update in-memory cache
                j_name, j_md5 = result
                self.cache.set(j_name, j_md5)
        # write cache to disk
        self.cache.save()
        logging.debug("Updated %d jobs in %ss",
                      len(jobs),
                      time.time() - step)
        logging.debug("Total run took %ss", (time.time() - orig))
        return jobs, len(jobs)

    @concurrent
    def parallel_update_job(self, job):
        self.update_job(job.name, job.output().decode('utf-8'))
        return (job.name, job.md5())

    ###########################
    # Promoted Builds related #
    ###########################

    def safe_promoted_build_name(self, promoted_build_name, parent_job_name):
        return '{}@promotion@{}'.format(parent_job_name, promoted_build_name)

    @property
    def promoted_builds(self):
        if self._promoted_builds is None:
            self._promoted_builds = []
            for job in self.jenkins.get_jobs():
                try:
                    promoted_builds = self.jenkins.get_promotions(job['name'])
                except jenkins.NotFoundException:
                    logger.debug(
                        'Job {} has no promoted builds'.format(job['name']))
                    promoted_builds = []

                for pb in promoted_builds:
                    pb['parent_job_name'] = job['name']
                    self._promoted_builds.append(pb)

        return self._promoted_builds

    @property
    def promoted_build_list(self):
        if self._promoted_build_list is None:
            self._promoted_build_list = \
                set(
                    self.safe_promoted_build_name(
                        pb['name'],
                        pb['parent_job_name']
                    ) for pb in self.promoted_builds)
        return self._promoted_build_list

    def update_promoted_build(self, promoted_build_name, parent_job_name, xml):
        if self.is_promoted_build(promoted_build_name, parent_job_name):
            logger.info("Reconfiguring jenkins promoted build '{p}' for job "
                        "'{j}'".format(j=parent_job_name,
                                       p=promoted_build_name))
            self.jenkins.reconfig_promotion(promoted_build_name,
                                            parent_job_name, xml)
        else:
            logger.info("Creating jenkins promoted build '{p}' for job "
                        "'{j}'".format(p=promoted_build_name,
                                       j=parent_job_name))
            self.jenkins.create_promotion(promoted_build_name,
                                          parent_job_name, xml)

    def is_promoted_build(self, promoted_build_name, parent_job_name):
        # first use cache
        pb_name = self.safe_promoted_build_name(promoted_build_name,
                                                parent_job_name)
        if pb_name in self.promoted_build_list:
            return True

        return self.jenkins.promotion_exists(promoted_build_name,
                                             parent_job_name)

    def promoted_build_changed(self, promoted_build):
        md5 = promoted_build.md5()

        changed = (
            self._jjb_config.builder['ignore_cache'] or
            self.cache.has_changed(
                self.safe_promoted_build_name(promoted_build.name,
                                              promoted_build.parent_job_name),
                md5)
        )
        if not changed:
            logger.debug("'{} - {}' has not changed".format(
                promoted_build.parent_job_name,
                promoted_build.name)
            )
        return changed

    def update_promoted_builds(self, xml_promoted_builds, output=None,
                               n_workers=None, config_xml=False):
        orig = time.time()

        num_promoted_builds = len(xml_promoted_builds)
        if num_promoted_builds == 0:
            return [], 0
        logger.info("Number of promoted builds jobs generated:  %d",
                    num_promoted_builds)
        xml_promoted_builds.sort(
            key=operator.attrgetter('parent_job_name', 'name'))

        if (output and not hasattr(output, 'write') and
                not os.path.isdir(output)):
            logger.info("Creating directory %s" % output)
            try:
                os.makedirs(output)
            except OSError:
                if not os.path.isdir(output):
                    raise

        if output:
            # ensure only wrapped once
            if hasattr(output, 'write'):
                output = utils.wrap_stream(output)

            for promoted_build in xml_promoted_builds:
                if hasattr(output, 'write'):
                    # `output` is a file-like object
                    logger.info("Promoted Build job & name:  %s, %s",
                                promoted_build.parent_job_name,
                                promoted_build.name)
                    logger.debug("Writing XML to '{0}'".format(output))
                    try:
                        output.write(promoted_build.output())
                    except IOError as exc:
                        if exc.errno == errno.EPIPE:
                            # EPIPE could happen if piping output to something
                            # that doesn't read the whole input (e.g.: the UNIX
                            # `head` command)
                            return
                        raise
                    continue

                if config_xml:
                    output_dir = os.path.join(output,
                                              promoted_build.parent_job_name,
                                              'promotion', 'process',
                                              promoted_build.name)
                    logger.info("Creating directory %s" % output_dir)
                    try:
                        os.makedirs(output_dir)
                    except OSError:
                        if not os.path.isdir(output_dir):
                            raise
                    output_fn = os.path.join(output_dir, 'config.xml')
                else:
                    output_fn = os.path.join(
                        output,
                        self.safe_promoted_build_name(
                            promoted_build.name,
                            promoted_build.parent_job_name)
                    )
                logger.debug("Writing XML to '{0}'".format(output_fn))
                with io.open(output_fn, 'w', encoding='utf-8') as f:
                    f.write(promoted_build.output().decode('utf-8'))
            return xml_promoted_builds, len(xml_promoted_builds)

        # Filter out the jobs that did not change
        logging.debug('Filtering %d promoted builds jobs for changed jobs',
                      len(xml_promoted_builds))
        step = time.time()
        promoted_builds = [pb for pb in xml_promoted_builds if
                           self.promoted_build_changed(pb)]
        logging.debug("Filtered for changed promoted builds jobs in %ss",
                      (time.time() - step))

        if not promoted_builds:
            return [], 0

        logging.debug('Updating promoted builds')
        step = time.time()
        p_params = [{'promoted_build': pb} for pb in promoted_builds]
        results = self.parallel_update_promoted_build(
            n_workers=n_workers,
            concurrent=p_params)
        logging.debug("Parsing results")
        # generalize the result parsing, as a concurrent job always returns a
        # list
        if len(p_params) in (1, 0):
            results = [results]
        for result in results:
            if isinstance(result, Exception):
                raise result
            else:
                pb_name, pb_md5 = result
                self.cache.set(pb_name, pb_md5)
        self.cache.save()
        logging.debug("Updated %d jobs in %ss",
                      len(promoted_builds),
                      time.time() - step)
        logging.debug("Total run took %ss", (time.time() - orig))
        return promoted_builds, len(promoted_builds)

    @concurrent
    def parallel_update_promoted_build(self, promoted_build):
        self.update_promoted_build(promoted_build.name,
                                   promoted_build.parent_job_name,
                                   promoted_build.output().decode('utf-8'))
        return (
            self.safe_promoted_build_name(promoted_build.name,
                                          promoted_build.parent_job_name),
            promoted_build.md5()
        )

    ################
    # View related #
    ################

    @property
    def views(self):
        if self._views is None:
            # populate views
            self._views = self.jenkins.get_views()
        return self._views

    @property
    def view_list(self):
        if self._view_list is None:
            self._view_list = set(view['name'] for view in self.views)
        return self._view_list

    def get_views(self, cache=True):
        if not cache:
            self._views = None
            self._view_list = None
        return self.views

    def is_view(self, view_name):
        # first use cache
        if view_name in self.view_list:
            return True

        # if not exists, use jenkins
        return self.jenkins.view_exists(view_name)

    def delete_view(self, view_name):
        if self.is_view(view_name):
            logger.info("Deleting jenkins view {}".format(view_name))
            self.jenkins.delete_view(view_name)

    def delete_views(self, views):
        if views is not None:
            logger.info("Removing jenkins view(s): %s" % ", ".join(views))
        for view in views:
            self.delete_view(view)
            if self.cache.is_cached(view):
                self.cache.set(view, '')
        self.cache.save()

    def delete_all_views(self):
        views = self.get_views()
        # Jenkins requires at least one view present. Don't remove the first
        # view as it is likely the default view.
        views.pop(0)
        logger.info("Number of views to delete:  %d", len(views))
        for view in views:
            self.delete_view(view['name'])
        # Need to clear the JJB cache after deletion
        self.cache.clear()

    def update_view(self, view_name, xml):
        if self.is_view(view_name):
            logger.info("Reconfiguring jenkins view {0}".format(view_name))
            self.jenkins.reconfig_view(view_name, xml)
        else:
            logger.info("Creating jenkins view {0}".format(view_name))
            self.jenkins.create_view(view_name, xml)

    def update_views(self, xml_views, output=None, n_workers=None,
                     config_xml=False):
        orig = time.time()

        logger.info("Number of views generated:  %d", len(xml_views))
        xml_views.sort(key=operator.attrgetter('name'))

        if output:
            # ensure only wrapped once
            if hasattr(output, 'write'):
                output = utils.wrap_stream(output)

            for view in xml_views:
                if hasattr(output, 'write'):
                    # `output` is a file-like object
                    logger.info("View name:  %s", view.name)
                    logger.debug("Writing XML to '{0}'".format(output))
                    try:
                        output.write(view.output())
                    except IOError as exc:
                        if exc.errno == errno.EPIPE:
                            # EPIPE could happen if piping output to something
                            # that doesn't read the whole input (e.g.: the UNIX
                            # `head` command)
                            return
                        raise
                    continue

                if config_xml:
                    output_dir = os.path.join(output, view.name)
                    logger.info("Creating directory %s" % output_dir)
                    try:
                        os.makedirs(output_dir)
                    except OSError:
                        if not os.path.isdir(output_dir):
                            raise
                    output_fn = os.path.join(output_dir, 'config.xml')
                else:
                    output_fn = os.path.join(output, view.name)
                logger.debug("Writing XML to '{0}'".format(output_fn))
                with io.open(output_fn, 'w', encoding='utf-8') as f:
                    f.write(view.output().decode('utf-8'))
            return xml_views, len(xml_views)

        # Filter out the views that did not change
        logging.debug('Filtering %d views for changed views',
                      len(xml_views))
        step = time.time()
        views = [view for view in xml_views
                 if self.changed(view)]
        logging.debug("Filtered for changed views in %ss",
                      (time.time() - step))

        if not views:
            return [], 0

        # Update the views
        logging.debug('Updating views')
        step = time.time()
        p_params = [{'view': view} for view in views]
        results = self.parallel_update_view(
            n_workers=n_workers,
            concurrent=p_params)
        logging.debug("Parsing results")
        # generalize the result parsing, as a concurrent view always returns a
        # list
        if len(p_params) in (1, 0):
            results = [results]
        for result in results:
            if isinstance(result, Exception):
                raise result
            else:
                # update in-memory cache
                v_name, v_md5 = result
                self.cache.set(v_name, v_md5)
        # write cache to disk
        self.cache.save()
        logging.debug("Updated %d views in %ss",
                      len(views),
                      time.time() - step)
        logging.debug("Total run took %ss", (time.time() - orig))
        return views, len(views)

    @concurrent
    def parallel_update_view(self, view):
        self.update_view(view.name, view.output().decode('utf-8'))
        return (view.name, view.md5())
