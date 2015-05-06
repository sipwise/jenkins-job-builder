#!/usr/bin/env python
# Copyright (C) 2013 Hewlett-Packard.
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

# Provides local yaml parsing classes and extend yaml module

"""Custom application specific yamls tags are supported to provide
enhancements when reading yaml configuration.

These allow inclusion of arbitrary files as a method of having blocks of data
managed separately to the yaml job configurations. A specific usage of this is
inlining scripts contained in separate files, although such tags may also be
used to simplify usage of macros or job templates.

The tag ``!include`` will treat the following string as file which should be
parsed as yaml configuration data.

Example:

    .. literalinclude:: /../../tests/localyaml/fixtures/include001.yaml

    contents of include001.yaml.inc:

    .. literalinclude:: /../../tests/yamlparser/fixtures/include001.yaml.inc


The tag ``!include-raw`` will treat the following file as a data blob, which
should be read into the calling yaml construct without any further parsing.
Any data in a file included through this tag, will be treated as string data.

Example:

    .. literalinclude:: /../../tests/localyaml/fixtures/include-raw001.yaml

    contents of include-raw001-hello-world.sh:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw001-hello-world.sh

    contents of include-raw001-vars.sh:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw001-vars.sh


The tag ``!include-raw-escape`` treats the given file as a data blob, which
should be escaped before being read in as string data. This allows
job-templates to use this tag to include scripts from files without
needing to escape braces in the original file.


Example:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-escaped001.yaml

    contents of include-raw001-hello-world.sh:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw001-hello-world.sh

    contents of include-raw001-vars.sh:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw001-vars.sh


Variants for the raw include tags ``!include-raw:`` and
``!include-raw-escape:`` accept a list of files. All of the specified files
are concatenated and included as string data.

Example:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-multi001.yaml

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-escaped-multi001.yaml

"""

import codecs
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import functools
import logging
import re
import os
import yaml
from yaml.constructor import BaseConstructor
from yaml import YAMLObject

logger = logging.getLogger(__name__)


class OrderedConstructor(BaseConstructor):
    """The default constructor class for PyYAML loading uses standard python
    dictionaries which can have randomized ordering enabled (default in
    CPython from version 3.3). The order of the XML elements being outputted
    is both important for tests and for ensuring predictable generation based
    on the source. This subclass overrides this behaviour to ensure that all
    dict's created make use of OrderedDict to have iteration of keys to always
    follow the order in which the keys were inserted/created.
    """

    def construct_yaml_map(self, node):
        data = OrderedDict()
        yield data
        value = self.construct_mapping(node)

        if isinstance(node, yaml.MappingNode):
            self.flatten_mapping(node)
        else:
            raise yaml.constructor.ConstructorError(
                None, None,
                'expected a mapping node, but found %s' % node.id,
                node.start_mark)

        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=False)
            try:
                hash(key)
            except TypeError as exc:
                raise yaml.constructor.ConstructorError(
                    'while constructing a mapping', node.start_mark,
                    'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=False)
            mapping[key] = value
        data.update(mapping)


class LocalLoader(OrderedConstructor, yaml.Loader):
    """Subclass for yaml.Loader which handles storing the search_path and
    escape_callback functions for use by the custom YAML objects to find files
    and escape the content where required.

    Constructor access a list of search paths to look under for the given
    file following each tag, taking the first match found. Search path by
    default will include the same directory as the yaml file and the current
    working directory.


    Loading::

        # use the load function provided in this module
        import local_yaml
        data = local_yaml.load(open(fn))


        # Loading by providing the alternate class to the default yaml load
        from local_yaml import LocalLoader
        data = yaml.load(open(fn), LocalLoader)

        # Loading with a search path
        from local_yaml import LocalLoader
        import functools
        data = yaml.load(open(fn), functools.partial(LocalLoader,
                        search_path=['path']))

    """

    def __init__(self, *args, **kwargs):
        # make sure to pop off any local settings before passing to
        # the parent constructor as any unknown args may cause errors.
        self.search_path = set()
        if 'search_path' in kwargs:
            for p in kwargs.pop('search_path'):
                logger.debug("Adding '{0}' to search path for include tags"
                             .format(p))
                self.search_path.add(os.path.normpath(p))

        if 'escape_callback' in kwargs:
            self.escape_callback = kwargs.pop('escape_callback')
        else:
            self.escape_callback = self._escape

        super(LocalLoader, self).__init__(*args, **kwargs)

        # constructor to preserve order of maps and ensure that the order of
        # keys returned is consistent across multiple python versions
        self.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                             type(self).construct_yaml_map)

        if hasattr(self.stream, 'name'):
            self.search_path.add(os.path.normpath(
                os.path.dirname(self.stream.name)))
        self.search_path.add(os.path.normpath(os.path.curdir))

    def _escape(self, data):
        return re.sub(r'({|})', r'\1\1', data)


class BaseYAMLObject(object):
    yaml_loader = LocalLoader
    yaml_dumper = yaml.Dumper


class YamlInclude(BaseYAMLObject, YAMLObject):
    yaml_tag = u'!include:'

    @classmethod
    def _find_file(cls, filename, search_path):
        for dirname in search_path:
            candidate = os.path.expanduser(os.path.join(dirname, filename))
            if os.path.isfile(candidate):
                logger.info("Including file '{0}' from path '{0}'"
                            .format(filename, dirname))
                return candidate
        return filename

    @classmethod
    def _from_file(cls, loader, node):
        filename = cls._find_file(loader.construct_yaml_str(node),
                                  loader.search_path)
        with open(filename, 'r') as f:
            data = yaml.load(f, functools.partial(cls.yaml_loader,
                                                  search_path=loader.search_path
                                                  ))
        return data

    @classmethod
    def from_yaml(cls, loader, node):
        if isinstance(node, yaml.ScalarNode):
            return cls._from_file(loader, node)
        elif isinstance(node, yaml.SequenceNode):
            return '\n'.join(cls._from_file(loader, scalar_node)
                             for scalar_node in node.value)
        else:
            raise yaml.constructor.ConstructorError(
                None, None, "expected either a sequence or scalar node, but "
                "found %s" % node.id, node.start_mark)


class YamlIncludeRaw(YamlInclude):
    yaml_tag = u'!include-raw:'

    @classmethod
    def _from_file(cls, loader, node):
        filename = cls._find_file(loader.construct_yaml_str(node),
                                  loader.search_path)
        try:
            with codecs.open(filename, 'r', 'utf-8') as f:
                data = f.read()
        except:
            logger.error("Failed to include file using search path: '{0}'"
                         .format(':'.join(loader.search_path)))
            raise
        return data


class YamlIncludeRawEscape(YamlIncludeRaw):
    yaml_tag = u'!include-raw-escape:'

    @classmethod
    def from_yaml(cls, loader, node):
        return loader.escape_callback(YamlIncludeRaw.from_yaml(loader, node))


class YamlIncludeDeprecated(YamlInclude):
    yaml_tag = u'!include'

    @classmethod
    def from_yaml(cls, loader, node):
        logger.warn("tag '%s' is deprecated, switch to using '%s'",
                    cls.yaml_tag, super(YamlIncludeDeprecated, cls).yaml_tag)
        return super(YamlIncludeDeprecated, cls).from_yaml(loader, node)


class YamlIncludeRawDeprecated(YamlIncludeRaw):
    yaml_tag = u'!include-raw'

    @classmethod
    def from_yaml(cls, loader, node):
        logger.warn("tag '%s' is deprecated, switch to using '%s'",
                    cls.yaml_tag, super(YamlIncludeRawDeprecated, cls).yaml_tag)
        return super(YamlIncludeRawDeprecated, cls).from_yaml(loader, node)


class YamlIncludeRawEscapeDeprecated(YamlIncludeRawEscape):
    yaml_tag = u'!include-raw-escape'

    @classmethod
    def from_yaml(cls, loader, node):
        logger.warn("tag '%s' is deprecated, switch to using '%s'",
                    cls.yaml_tag, super(YamlIncludeRawEscapeDeprecated,
                                        cls).yaml_tag)
        return super(YamlIncludeRawEscapeDeprecated, cls).from_yaml(loader,
                                                                    node)


def load(stream, **kwargs):
    return yaml.load(stream, functools.partial(LocalLoader, **kwargs))
