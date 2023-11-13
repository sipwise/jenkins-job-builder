#!/usr/bin/env python
# Copyright (C) 2015 OpenStack, LLC.
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

# Manage Jenkins plugin module registry.

import inspect
import logging
import operator
import pkg_resources
import re
import types

from six import PY2

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.expander import Expander
from jenkins_jobs.yaml_objects import BaseYamlObject

__all__ = ["ModuleRegistry"]

logger = logging.getLogger(__name__)

getargspec = inspect.getargspec if PY2 else inspect.getfullargspec


class ModuleRegistry(object):
    _entry_points_cache = {}
    _component_type_cache = {}

    def __init__(self, jjb_config, plugins_list=None):
        self.modules = []
        self.modules_by_component_type = {}
        self.handlers = {}
        self.jjb_config = jjb_config
        self.masked_warned = {}
        self._macros = {}
        self._expander = Expander(jjb_config)

        if plugins_list is None:
            self.plugins_dict = {}
        else:
            self.plugins_dict = self._get_plugins_info_dict(plugins_list)

        for entrypoint in pkg_resources.iter_entry_points(group="jenkins_jobs.modules"):
            Mod = entrypoint.load()
            mod = Mod(self)
            self.modules.append(mod)
            self.modules.sort(key=operator.attrgetter("sequence"))
            if mod.component_type is not None:
                self.modules_by_component_type[mod.component_type] = entrypoint

    @staticmethod
    def _get_plugins_info_dict(plugins_list):
        def mutate_plugin_info(plugin_info):
            """
            We perform mutations on a single member of plugin_info here, then
            return a dictionary with the longName and shortName of the plugin
            mapped to its plugin info dictionary.
            """
            version = plugin_info.get("version", "0")
            plugin_info["version"] = re.sub(
                r"(.*)-(?:SNAPSHOT|BETA).*", r"\g<1>.preview", version
            )

            if isinstance(
                pkg_resources.parse_version(plugin_info["version"]),
                pkg_resources.extern.packaging.version.LegacyVersion,
            ):
                plugin_info["version"] = plugin_info["version"].replace("-", "+")
            if isinstance(
                pkg_resources.parse_version(plugin_info["version"]),
                pkg_resources.extern.packaging.version.LegacyVersion,
            ):
                plugin_name = plugin_info.get(
                    "shortName", plugin_info.get("longName", None)
                )
                if plugin_name:
                    logger.warning(
                        "Version %s for plugin %s is being treated as a LegacyVersion"
                        % (plugin_info["version"], plugin_name)
                    )
                else:
                    logger.warning(
                        "Version %s is being treated as a LegacyVersion"
                        % plugin_info["version"]
                    )

            aliases = []
            for key in ["longName", "shortName"]:
                value = plugin_info.get(key, None)
                if value is not None:
                    aliases.append(value)

            plugin_info_dict = {}
            for name in aliases:
                plugin_info_dict[name] = plugin_info

            return plugin_info_dict

        list_of_dicts = [mutate_plugin_info(v) for v in plugins_list]

        plugins_info_dict = {}
        for d in list_of_dicts:
            plugins_info_dict.update(d)

        return plugins_info_dict

    @staticmethod
    def _filter_kwargs(func, **kwargs):
        arg_spec = getargspec(func)
        for name in list(kwargs.keys()):
            if name not in arg_spec.args:
                del kwargs[name]
        return kwargs

    def get_plugin_info(self, plugin_name):
        """Provide information about plugins within a module's impl of Base.gen_xml.

        The return value is a dictionary with data obtained directly from a
        running Jenkins instance.
        This allows module authors to differentiate generated XML output based
        on information such as specific plugin versions.

        :arg str plugin_name: Either the shortName or longName of a plugin
          as see in a query that looks like:
          ``http://<jenkins-hostname>/pluginManager/api/json?pretty&depth=2``

        During a 'test' run, it is possible to override JJB's query to a live
        Jenkins instance by passing it a path to a file containing a YAML list
        of dictionaries that mimics the plugin properties you want your test
        output to reflect::

          jenkins-jobs test -p /path/to/plugins-info.yaml

        Below is example YAML that might be included in
        /path/to/plugins-info.yaml.

        .. literalinclude:: /../../tests/cmd/fixtures/plugins-info.yaml

        """
        return self.plugins_dict.get(plugin_name, {})

    def registerHandler(self, category, name, method):
        cat_dict = self.handlers.get(category, {})
        if not cat_dict:
            self.handlers[category] = cat_dict
        cat_dict[name] = method

    def getHandler(self, category, name):
        return self.handlers[category][name]

    @property
    def macros(self):
        return self._macros

    def set_macros(self, macros):
        self._macros = macros

    def amend_job_dicts(self, job_data_list):
        while True:
            changed = False
            for job in job_data_list:
                for module in self.modules:
                    if module.amend_job_dict(job.data):
                        changed = True
            if not changed:
                break

    def get_component_list_type(self, entry_point):
        if entry_point in self._component_type_cache:
            return self._component_type_cache[entry_point]

        # pkg_resources.EntryPoint.load() is costly, cache it.
        component_list_type = entry_point.load().component_list_type
        logging.info("Caching type %s of %s", component_list_type, entry_point)
        self._component_type_cache[entry_point] = component_list_type

        return component_list_type

    def dispatch(
        self, component_type, xml_parent, component, template_data={}, job_data=None
    ):
        """This is a method that you can call from your implementation of
        Base.gen_xml or component.  It allows modules to define a type
        of component, and benefit from extensibility via Python
        entry points and Jenkins Job Builder :ref:`Macros <macro>`.

        :arg str component_type: the name of the component
          (e.g., `builder`)
        :arg xml_parent: the parent XML element
        :arg component: component definition
        :arg dict template_data: values that should be interpolated into
          the component definition
        :arg dict job_data: full job definition

        See :py:class:`jenkins_jobs.modules.base.Base` for how to register
        components of a module.

        See the Publishers module for a simple example of how to use
        this method.
        """

        if component_type not in self.modules_by_component_type:
            raise JenkinsJobsException(
                "Unknown component type: " "'{0}'.".format(component_type)
            )

        entry_point = self.modules_by_component_type[component_type]
        component_list_type = self.get_component_list_type(entry_point)

        if isinstance(component, dict):
            # The component is a singleton dictionary of name: dict(args)
            name, component_data = next(iter(component.items()))
            if template_data:
                paramdict = {}
                paramdict.update(template_data)
                paramdict.update(job_data or {})
        else:
            # The component is a simple string name, eg "run-tests"
            name = component
            component_data = {}

        # Look for a component function defined in an entry point
        eps = self._entry_points_cache.get(component_list_type)
        if eps is None:
            eps = self._load_eps(
                component_list_type, component_type, entry_point, eps, name
            )

        macro_dict = self.macros.get(component_type, {})
        macro = macro_dict.get(name)
        if macro:
            self._dispatch_macro(
                component_data, component_type, eps, job_data, macro, name, xml_parent
            )
        elif name in eps:
            try:
                func = eps[name]
                kwargs = self._filter_kwargs(func, job_data=job_data)
                func(self, xml_parent, component_data, **kwargs)
            except JenkinsJobsException as x:
                raise x.with_context(
                    f"In {component_type} {name!r}",
                    pos=component.pos,
                )
        else:
            raise JenkinsJobsException(
                "Unknown entry point or macro '{0}' "
                "for component type: '{1}'.".format(name, component_type)
            )

    def _dispatch_macro(
        self, component_data, component_type, eps, job_data, macro, name, xml_parent
    ):
        if name in eps and name not in self.masked_warned:
            self.masked_warned[name] = True
            logger.warning(
                "You have a macro ('%s') defined for '%s' "
                "component type that is masking an inbuilt "
                "definition" % (name, component_type)
            )
        if component_data is None:
            component_data = {}
        expander_params = {**component_data, **(job_data or {})}
        elements = macro.elements
        if isinstance(elements, BaseYamlObject):
            # Expand !j2-yaml element right below macro body.
            elements = elements.expand(self._expander, expander_params)
        for b in elements:
            try:
                element = self._expander.expand(b, expander_params)
            except JenkinsJobsException as x:
                raise x.with_context(
                    f"While expanding macro {name!r}",
                    pos=macro.pos,
                )
            # Pass component_data in as template data to this function
            # so that if the macro is invoked with arguments,
            # the arguments are interpolated into the real defn.
            self.dispatch(
                component_type,
                xml_parent,
                element,
                component_data,
                job_data=job_data,
            )

    def _load_eps(self, component_list_type, component_type, entry_point, eps, name):
        logging.debug("Caching entrypoints for %s" % component_list_type)
        module_eps = []
        # auto build entry points by inferring from base component_types
        mod = pkg_resources.EntryPoint(
            "__all__", entry_point.module_name, dist=entry_point.dist
        )
        Mod = mod.load()
        func_eps = [
            Mod.__dict__.get(a)
            for a in dir(Mod)
            if isinstance(Mod.__dict__.get(a), types.FunctionType)
        ]
        for func_ep in func_eps:
            try:
                # extract entry point based on docstring
                name_line = func_ep.__doc__.split("\n")
                if not name_line[0].startswith("yaml:"):
                    logger.debug("Ignoring '%s' as an entry point" % name_line)
                    continue
                ep_name = name_line[0].split(" ")[1]
            except (AttributeError, IndexError):
                # AttributeError by docstring not being defined as
                # a string to have split called on it.
                # IndexError raised by name_line not containing anything
                # after the 'yaml:' string.
                logger.debug(
                    "Not including func '%s' as an entry point" % func_ep.__name__
                )
                continue

            module_eps.append(
                pkg_resources.EntryPoint(
                    ep_name,
                    entry_point.module_name,
                    dist=entry_point.dist,
                    attrs=(func_ep.__name__,),
                )
            )
            logger.debug(
                "Adding auto EP '%s=%s:%s'"
                % (ep_name, entry_point.module_name, func_ep.__name__)
            )
        # load from explicitly defined entry points
        module_eps.extend(
            list(
                pkg_resources.iter_entry_points(
                    group="jenkins_jobs.{0}".format(component_list_type)
                )
            )
        )
        eps = {}
        for module_ep in module_eps:
            if module_ep.name in eps:
                raise JenkinsJobsException(
                    "Duplicate entry point found for component type: "
                    "'{0}', '{0}',"
                    "name: '{1}'".format(component_type, name)
                )

            eps[module_ep.name] = module_ep.load()
        # cache both sets of entry points
        self._entry_points_cache[component_list_type] = eps
        logger.debug("Cached entry point group %s = %s", component_list_type, eps)
        return eps
