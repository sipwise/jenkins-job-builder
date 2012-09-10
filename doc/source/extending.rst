Extending
=========

Jenkins Job Builder is quite modular.  It is easy to add new
attributes to existing actions, a new module to support a Jenkins
plugin, or include locally defined methods to deal with an
idiosyncratic build system.

XML Processing
--------------

Most of the work of building XML from the YAML configuration file is
handled by individual functions that implement a single
characteristic.  For example, see the
``jenkins_jobs/modules/builders.py`` file for the Python module that
implements the standard Jenkins builders.  The ``shell`` function at
the top of the file implements the standard `Execute a shell` build
step.  All of the YAML to XML functions in Jenkins Job Builder have
the same signature: 

.. py:function:: handler(parser, xml_parent, data)
  :noindex:

  :arg YAMLParser parser: the jenkins jobs YAML parser
  :arg Element xml_parent: this attribute's parent XML element
  :arg dict data: the YAML data structure for this attribute and below

The function is expected to examine the YAML data structure and create
new XML nodes and attach them to the xml_parent element.  This general
pattern is applied throughout the included modules.

Modules
-------

Nearly all of Jenkins Job Builder is implemented in modules.  The main
program has no concept of builders, publishers, properties, or any
other aspects of job definition.  Each of those building blocks is
defined in a module, and due to the use of setuptools entry points,
most modules are easily extensible with new actions.

To add a new module, define a class that inherits from
:py:class:`jenkins_jobs.modules.base.Base`

.. autoclass:: jenkins_jobs.modules.base.Base
