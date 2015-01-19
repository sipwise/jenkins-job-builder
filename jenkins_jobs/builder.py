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
import os
import operator
import sys
import hashlib
import yaml
import xml.etree.ElementTree as XML
import xml
from xml.dom import minidom
import jenkins
import re
import pkg_resources
import logging
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.yml.parser import YamlParser
from jenkins_jobs.utils import matches

logger = logging.getLogger(__name__)
MAGIC_MANAGE_STRING = "<!-- Managed by Jenkins Job Builder -->"


# Python 2.6's minidom toprettyxml produces broken output by adding extraneous
# whitespace around data. This patches the broken implementation with one taken
# from Python > 2.7.3
def writexml(self, writer, indent="", addindent="", newl=""):
    # indent = current indentation
    # addindent = indentation to add to higher levels
    # newl = newline string
    writer.write(indent + "<" + self.tagName)

    attrs = self._get_attributes()
    a_names = attrs.keys()
    a_names.sort()

    for a_name in a_names:
        writer.write(" %s=\"" % a_name)
        minidom._write_data(writer, attrs[a_name].value)
        writer.write("\"")
    if self.childNodes:
        writer.write(">")
        if (len(self.childNodes) == 1 and
                self.childNodes[0].nodeType == minidom.Node.TEXT_NODE):
            self.childNodes[0].writexml(writer, '', '', '')
        else:
            writer.write(newl)
            for node in self.childNodes:
                node.writexml(writer, indent + addindent, addindent, newl)
            writer.write(indent)
        writer.write("</%s>%s" % (self.tagName, newl))
    else:
        writer.write("/>%s" % (newl))

# PyXML xml.__name__ is _xmlplus. Check that if we don't have the default
# system version of the minidom, then patch the writexml method
if sys.version_info[:3] < (2, 7, 3) or xml.__name__ != 'xml':
    minidom.Element.writexml = writexml


class FauxParser:
    """
    Essentially a stub class to emulate the old spaghetti code yaml parser that
    did so much more than parse yaml....
    """

    def __init__(self):
        self.registry = None
        self.data = None


def generateXML(raw_yaml_data, registry, jobs):
    """
    Given a list of jobs and a module registry, generate a list of XmlJob's
    representing each job.
    """
    xmljobs = []
    for job in jobs:
        xmljobs.append(getXMLForJob(raw_yaml_data, registry, job))
    return xmljobs


def getXMLForJob(raw_yaml_data, registry, job):
    kind = job.get('project-type', 'freestyle')

    faux_parser = FauxParser()
    setattr(faux_parser, "registry", registry)
    setattr(faux_parser, "data", raw_yaml_data)

    for ep in pkg_resources.iter_entry_points(
            group='jenkins_jobs.projects', name=kind):
        Mod = ep.load()
        mod = Mod(registry)
        xml = mod.root_xml(job)
        gen_xml(faux_parser, xml, job)
        xmljob = XmlJob(xml, job['name'])
        return xmljob


def gen_xml(parser, xml, data):
    for module in parser.registry.modules:
        if hasattr(module, 'gen_xml'):
            module.gen_xml(parser, xml, data)


class ModuleRegistry(object):
    entry_points_cache = {}

    def __init__(self, config):
        self.modules = []
        self.modules_by_component_type = {}
        self.handlers = {}
        self.global_config = config

        for entrypoint in pkg_resources.iter_entry_points(
                group='jenkins_jobs.modules'):
            Mod = entrypoint.load()
            mod = Mod(self)
            self.modules.append(mod)
            self.modules.sort(key=operator.attrgetter('sequence'))
            if mod.component_type is not None:
                self.modules_by_component_type[mod.component_type] = mod

    def registerHandler(self, category, name, method):
        cat_dict = self.handlers.get(category, {})
        if not cat_dict:
            self.handlers[category] = cat_dict
        cat_dict[name] = method

    def getHandler(self, category, name):
        return self.handlers[category][name]

    def dispatch(self, component_type,
                 parser, xml_parent,
                 component, template_data={}):
        """This is a method that you can call from your implementation of
        Base.gen_xml or component.  It allows modules to define a type
        of component, and benefit from extensibility via Python
        entry points and Jenkins Job Builder :ref:`Macros <macro>`.

        :arg string component_type: the name of the component
          (e.g., `builder`)
        :arg YAMLParser parser: the global YAML Parser
        :arg Element xml_parent: the parent XML element
        :arg dict template_data: values that should be interpolated into
          the component definition

        See :py:class:`jenkins_jobs.modules.base.Base` for how to register
        components of a module.

        See the Publishers module for a simple example of how to use
        this method.
        """

        if component_type not in self.modules_by_component_type:
            raise JenkinsJobsException("Unknown component type: "
                                       "'{0}'.".format(component_type))

        component_list_type = self.modules_by_component_type[component_type] \
            .component_list_type

        if isinstance(component, dict):
            # The component is a singleton dictionary of name: dict(args)
            name, component_data = next(iter(component.items()))
            if template_data:
                # Template data contains values that should be interpolated
                # into the component definition
                s = yaml.dump(component_data, default_flow_style=False)
                s = s.format(**template_data)
                component_data = yaml.load(s)
        else:
            # The component is a simple string name, eg "run-tests"
            name = component
            component_data = {}

        # Look for a component function defined in an entry point
        eps = ModuleRegistry.entry_points_cache.get(component_list_type)
        if eps is None:
            module_eps = list(pkg_resources.iter_entry_points(
                group='jenkins_jobs.{0}'.format(component_list_type)))
            eps = {}
            for module_ep in module_eps:
                if module_ep.name in eps:
                    raise JenkinsJobsException(
                        "Duplicate entry point found for component type: "
                        "'{0}', '{0}',"
                        "name: '{1}'".format(component_type, name))
                eps[module_ep.name] = module_ep

            ModuleRegistry.entry_points_cache[component_list_type] = eps
            logger.debug("Cached entry point group %s = %s",
                         component_list_type, eps)

        if name in eps:
            func = eps[name].load()
            func(parser, xml_parent, component_data)
        else:
            # Otherwise, see if it's defined as a macro
            thing = parser.data.get(component_type, {})
            component = thing.get(name)
            if component:
                for b in component[component_list_type]:
                    # Pass component_data in as template data to this function
                    # so that if the macro is invoked with arguments,
                    # the arguments are interpolated into the real defn.
                    self.dispatch(component_type,
                                  parser, xml_parent, b, component_data)
            else:
                raise JenkinsJobsException("Unknown entry point or macro '{0}'"
                                           " for component type: '{1}'.".
                                           format(name, component_type))


class XmlJob(object):
    def __init__(self, xml, name):
        self.xml = xml
        self.name = name

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    def output(self):
        out = minidom.parseString(XML.tostring(self.xml, encoding='UTF-8'))
        return out.toprettyxml(indent='  ', encoding='utf-8')


class CacheStorage(object):
    # ensure each instance of the class has a reference to the required
    # modules so that they are available to be used when the destructor
    # is being called since python will not guarantee that it won't have
    # removed global module references during teardown.
    _yaml = yaml
    _logger = logger

    def __init__(self, jenkins_url, flush=False):
        cache_dir = self.get_cache_dir()
        # One cache per remote Jenkins URL:
        host_vary = re.sub('[^A-Za-z0-9\-\~]', '_', jenkins_url)
        self.cachefilename = os.path.join(
            cache_dir, 'cache-host-jobs-' + host_vary + '.yml')
        if flush or not os.path.isfile(self.cachefilename):
            self.data = {}
        else:
            with file(self.cachefilename, 'r') as yfile:
                self.data = yaml.load(yfile)
        logger.debug("Using cache: '{0}'".format(self.cachefilename))

    @staticmethod
    def get_cache_dir():
        home = os.path.expanduser('~')
        if home == '~':
            raise OSError('Could not locate home folder')
        xdg_cache_home = os.environ.get('XDG_CACHE_HOME') or \
            os.path.join(home, '.cache')
        path = os.path.join(xdg_cache_home, 'jenkins_jobs')
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def set(self, job, md5):
        self.data[job] = md5

    def is_cached(self, job):
        if job in self.data:
            return True
        return False

    def has_changed(self, job, md5):
        if job in self.data and self.data[job] == md5:
            return False
        return True

    def save(self):
        # check we initialized sufficiently in case called via __del__
        # due to an exception occurring in the __init__
        if getattr(self, 'data', None) is not None:
            try:
                with open(self.cachefilename, 'w') as yfile:
                    self._yaml.dump(self.data, yfile)
            except Exception as e:
                self._logger.error("Failed to write to cache file '%s' on "
                                   "exit: %s" % (self.cachefilename, e))
            else:
                self._logger.info("Cache saved")
                self._logger.debug("Cache written out to '%s'" %
                                   self.cachefilename)

    def __del__(self):
        self.save()


class Jenkins(object):
    def __init__(self, url, user, password):
        self.jenkins = jenkins.Jenkins(url, user, password)

    def update_job(self, job_name, xml):
        if self.is_job(job_name):
            logger.info("Reconfiguring jenkins job {0}".format(job_name))
            self.jenkins.reconfig_job(job_name, xml)
        else:
            logger.info("Creating jenkins job {0}".format(job_name))
            self.jenkins.create_job(job_name, xml)

    def is_job(self, job_name):
        return self.jenkins.job_exists(job_name)

    def get_job_md5(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        return hashlib.md5(xml).hexdigest()

    def delete_job(self, job_name):
        if self.is_job(job_name):
            logger.info("Deleting jenkins job {0}".format(job_name))
            self.jenkins.delete_job(job_name)

    def get_jobs(self):
        return self.jenkins.get_jobs()

    def is_managed(self, job_name):
        xml = self.jenkins.get_job_config(job_name)
        try:
            out = XML.fromstring(xml)
            description = out.find(".//description").text
            return description.endswith(MAGIC_MANAGE_STRING)
        except (TypeError, AttributeError):
            pass
        return False


class Builder(object):
    def __init__(self, jenkins_url, jenkins_user, jenkins_password,
                 config=None, ignore_cache=False, flush_cache=False):
        self.jenkins = Jenkins(jenkins_url, jenkins_user, jenkins_password)
        self.cache = CacheStorage(jenkins_url, flush=flush_cache)
        self.global_config = config
        self.ignore_cache = ignore_cache
        self.registry = ModuleRegistry(self.global_config)
        self.parser = YamlParser(self.global_config)

    def delete_old_managed(self, keep):
        jobs = self.jenkins.get_jobs()
        for job in jobs:
            if job['name'] not in keep and \
                    self.jenkins.is_managed(job['name']):
                logger.info("Removing obsolete jenkins job {0}"
                            .format(job['name']))
                self.delete_job(job['name'])
            else:
                logger.debug("Ignoring unmanaged jenkins job %s",
                             job['name'])

    def delete_job(self, glob_name, fn=None):
        if fn:
            self.parser.load_files(fn)
            self.parser.expandYaml(self.registry, glob_name)
            jobs = [j['name']
                    for j in self.parser.jobs
                    if matches(j['name'], [glob_name])]
        else:
            jobs = [glob_name]

        if jobs is not None:
            logger.info("Removing jenkins job(s): %s" % ", ".join(jobs))
        for job in jobs:
            self.jenkins.delete_job(job)
            if(self.cache.is_cached(job)):
                self.cache.set(job, '')

    def delete_all_jobs(self):
        jobs = self.jenkins.get_jobs()
        for job in jobs:
            self.delete_job(job['name'])

    def update_job(self, input_fn, names=None, output=None):
        self.parser.load_files(input_fn)
        self.parser.expandYaml(self.registry, names)
        xmljobs = generateXML(self.parser.data,
                              self.registry, self.parser.jobs)

        xmljobs.sort(key=operator.attrgetter('name'))

        for job in xmljobs:
            if names and not matches(job.name, names):
                continue
            if output:
                if hasattr(output, 'write'):
                    # `output` is a file-like object
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

                output_dir = output

                try:
                    os.makedirs(output_dir)
                except OSError:
                    if not os.path.isdir(output_dir):
                        raise

                output_fn = os.path.join(output_dir, job.name)
                logger.debug("Writing XML to '{0}'".format(output_fn))
                f = open(output_fn, 'w')
                f.write(job.output())
                f.close()
                continue
            md5 = job.md5()
            if (self.jenkins.is_job(job.name)
                    and not self.cache.is_cached(job.name)):
                old_md5 = self.jenkins.get_job_md5(job.name)
                self.cache.set(job.name, old_md5)

            if self.cache.has_changed(job.name, md5) or self.ignore_cache:
                self.jenkins.update_job(job.name, job.output())
                self.cache.set(job.name, md5)
            else:
                logger.debug("'{0}' has not changed".format(job.name))
        return xmljobs
