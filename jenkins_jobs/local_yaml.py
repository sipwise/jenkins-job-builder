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


The tag ``!include-raw`` will treat the following file as a data blob, which
should be read into the calling yaml construct without any further parsing.
Any data in a file included through this tag, will be treated as string data.

Example:

    .. literalinclude:: /../../tests/localyaml/fixtures/include-raw001.yaml


The tag ``!include-raw-escape`` treats the given file as a data blob, which
should be escaped before being read in as string data. This allows
job-templates to use this tag to include scripts from files without
needing to escape braces in the original file.


Example:

    .. literalinclude::
        /../../tests/localyaml/fixtures/include-raw-escaped001.yaml


Includes support for lazy loading of files where the path contains a
placeholder to be substituted after initial load and before final parsing of
the resulting data.


Example:

    .. literalinclude:: /../../tests/yamlparser/fixtures/lazy-load-jobs001.yaml

"""

import functools
import logging
import re
import os
import yaml

logger = logging.getLogger(__name__)


class LocalLoader(yaml.Loader):
    """Subclass for yaml.Loader which handles the local tags 'include',
    'include-raw' and 'include-raw-escaped' to specify a file to include data
    from and whether to parse it as additional yaml, treat it as a data blob
    or additionally escape the data contained. These are specified in yaml
    files by "!include path/to/file.yaml".

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
            self._escape = kwargs.pop('escape_callback')

        super(LocalLoader, self).__init__(*args, **kwargs)

        # Add tag constructors
        self.add_constructor('!include', self._include_tag)
        self.add_constructor('!include-raw', self._include_raw_tag)
        self.add_constructor('!include-raw-escape',
                             self._include_raw_escape_tag)

        if isinstance(self.stream, file):
            self.search_path.add(os.path.normpath(
                os.path.dirname(self.stream.name)))
        self.search_path.add(os.path.normpath(os.path.curdir))

    def _find_file(self, filename):
        for dirname in self.search_path:
            candidate = os.path.expanduser(os.path.join(dirname, filename))
            if os.path.isfile(candidate):
                logger.info("Including file '{0}' from path '{0}'"
                            .format(filename, dirname))
                return candidate
        return filename

    def _lazy_load(self, tag, node_str):
        logger.info("Lazy loading of file template '{0}' enabled"
                    .format(node_str))
        return LazyLoader(("!%s %s" % (tag, node_str),
                           functools.partial(LocalLoader,
                                             search_path=self.search_path
                                             )))

    def _include_tag(self, loader, node):
        node_str = loader.construct_yaml_str(node)
        try:
            node_str.format()
        except KeyError:
            return self._lazy_load("include", node_str)

        filename = self._find_file(node_str)
        with open(filename, 'r') as f:
            data = yaml.load(f, functools.partial(LocalLoader,
                                                  search_path=self.search_path
                                                  ))
        return data

    def _include_raw_tag(self, loader, node):
        node_str = loader.construct_yaml_str(node)
        try:
            node_str.format()
        except KeyError:
            return self._lazy_load("include-raw", node_str)

        filename = self._find_file(node_str)
        try:
            with open(filename, 'r') as f:
                data = f.read()
        except:
            logger.error("Failed to include file using search path: '{0}'"
                         .format(':'.join(self.search_path)))
            raise
        return data

    def _include_raw_escape_tag(self, loader, node):
        data = self._include_raw_tag(loader, node)
        if isinstance(data, LazyLoader):
            return data
        else:
            return self._escape(data)

    def _escape(self, data):
        return re.sub(r'({|})', r'\1\1', data)


class LazyLoader(str):
    """Helper class to provide lazy loading of files included using !include*
    tags where the path to the given file contains unresolved placeholders.
    """

    def __init__(self, data):
        # str subclasses can only have one argument, so assume it is a tuple
        # being passed and unpack as needed
        self._tag, self._loader = data

    def __str__(self):
        return self._tag

    def __repr__(self):
        return self._tag

    def format(self, *args, **kwargs):
        return yaml.load(self._tag.format(*args, **kwargs), self._loader)


def load(stream, **kwargs):
    return yaml.load(stream, functools.partial(LocalLoader, **kwargs))
