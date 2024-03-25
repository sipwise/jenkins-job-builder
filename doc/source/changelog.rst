Changelog
==========

Release 6.2.0
-------------

Features added
~~~~~~~~~~~~~~

* `--delete-old` flag for `update` cli command is now deletes obsolete views also, not only jobs.
* Add `--force` flag to `delete-all` cli command to allow it's usage in scripts.

Bugs fixed
~~~~~~~~~~

* Do not delete obsolete jobs when `--views-only` option specified.
* Add readthedocs configuration file. RTD now requires it. Fixes documentation build on RTD.

Release 6.1.0
-------------

Features added
~~~~~~~~~~~~~~

* Update TAP publisher plugin (by Kienan Stewart).
* Add tags: ``!include-raw-verbatim:`` and ``!include-raw-expand:``. Tags ``!include-raw:`` and ``!include-raw-escape:`` are now deprecated.
* Macros can now use parameters specified in defaults, the same way as job-templates.
  See this examples:

  * `macro-uses-global-defaults.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/910877/4/tests/yamlparser/job_fixtures/macro-uses-global-defaults.yaml>`_
  * `macro-uses-custom-defaults.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/910877/4/tests/yamlparser/job_fixtures/macro-uses-custom-defaults.yaml>`_

* Macros can now define default parameters in their body the same way as jobs, job-templates and projects.
  See this example:
  `macro-parameter-precenence.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/910880/5/tests/yamlparser/job_fixtures/macro-parameter-precenence.yaml>`_

.. note::
   After moving to 6.1.0 release, to remove deprecation warnings make these adjustments to your JJB sources:

   * Replace tags ``!include-raw:`` -> ``!include-raw-expand:``.
   * Replace tags ``!include-raw-escape:`` -> ``!include-raw-verbatim:``.

Release 6.0.0
-------------

Changes breaking backward compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Jobs are now expanded the same way as job templates.
* Macros without parameters are now expanded the same way as macros with parameters.
* Tags ``!include-raw``: and ``!include-raw-escape:`` should now be used the same way in jobs
  and macros without parameters as they are used in job templates and macros with parameters.

See also these stories:

* Expand jobs the same way as job templates are expanded (`Story 2010963 <https://storyboard.openstack.org/#!/story/2010963>`_).
* Expand macros even if called without arguments (`Story 2010588 <https://storyboard.openstack.org/#!/story/2010588>`_).

.. note::
   To move to 6.0.0 release, make these adjustments to your JJB sources:

   For every job and macro without parameters:

   * Duplicate curly braces: ``{...}`` -> ``{{...}}``.
   * Replace tags ``!include-raw:`` -> ``!include-raw-escape:``.

   See this example: `job-and-macro-expansions.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/900858/8/tests/yamlparser/job_fixtures/job-and-macro-expansions.yaml>`_.

Also, global defaults are now used when expanding job elements the same way as they are used for expanding job templates.
See this example:
`concat_defaults003_job.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/901665/7/tests/yamlparser/job_fixtures/concat_defaults003_job.yaml>`_
`concat_defaults003_job.xml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/901665/7/tests/yamlparser/job_fixtures/concat_defaults003_job.xml>`_


Release 5.1.0
-------------

Features added
~~~~~~~~~~~~~~

* Added macro call context to errors.
* Removed cap on setuptools version (`Story 2010842 <https://storyboard.openstack.org/#!/story/2010842>`_).
* Added support for Python 3.11.

Bugs fixed
~~~~~~~~~~

* Restored macros support for notifications. It was lost with 5.0.0 release.
* Folder defined at defaults is ignored
  (`Story 2010984 <https://storyboard.openstack.org/#!/story/2010984>`_).
* Wrong files adding by tag !include-raw (include-raw-escape, etc)
  (`Story 2010711 <https://storyboard.openstack.org/#!/story/2010711>`_) (by Maxim Trunov).
* On multibranch projects ignore-tags-older-than and ignore-tags-newer-than are inverted
  (`Story 2004614 <https://storyboard.openstack.org/#!/story/2004614>`_) (by Michal Szelag).
* Legacy plugin version comparison (`Story 2010990 <https://storyboard.openstack.org/#!/story/2010990>`_).
  This also closed:

  - `Story 2009943 <https://storyboard.openstack.org/#!/story/2009943>`_:
    PostBuildScript Plugin Version Format Change in 3.1.0-375.v3db_cd92485e1 Breaks Job Builder Version Compares.
  - `Story 2009819 <https://storyboard.openstack.org/#!/story/2009819>`_:
    Slack Plugin Version Format Change in 602.v0da_f7458945d Breaks Job Builder Version Compares.

* Support for obsolete format of pre-scm-buildstep

Release 5.0.4
-------------

Bugs fixed
~~~~~~~~~~

* Dimension parameter overrides bug (`Story 2010883 <https://storyboard.openstack.org/#!/story/2010883>`_).

Release 5.0.3
-------------

Features added
~~~~~~~~~~~~~~

* Added tokenCredentialId parameter support to generic-webhook-trigger (by Oleg Stiplin).
* Axis in project parameters are now expanded before enumerating it's jobs.
  For example, see test
  `include-param.yaml <https://opendev.org/jjb/jenkins-job-builder/src/branch/master/tests/yamlparser/job_fixtures/include-param.yaml>`_
  (`include-param.yaml.inc <https://opendev.org/jjb/jenkins-job-builder/src/branch/master/tests/yamlparser/job_fixtures/include-param.yaml.inc>`_)


Release 5.0.2
-------------

Bugs fixed
~~~~~~~~~~

* Macro call with null parameters.

Release 5.0.1
-------------

Bugs fixed
~~~~~~~~~~

* JJB fails on empty YAML file

Release 5.0.0
-------------

Changes breaking backward compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* YAML parser/expander is rewritten.

  - More aggressive parameter expansion. This may lead to parameters expanded in places where they were not expanded before.
    See changes in this test for examples:

    * `inter-parameter-expansion.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/inter-parameter-expansion.yaml>`_
    * `inter-parameter-expansion.xml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/inter-parameter-expansion.xml>`_

  - Top-level elements, which is not known to parser (such as 'job', 'view', 'project' etc), are now lead to parse failures.
    **Fix:** Prepend them with underscore to be ignored by parser. For example:

    * `custom_retain_anchors_include001.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/loader/fixtures/custom_retain_anchors_include001.yaml>`_

  - Files included using ``!include-raw:`` elements and having formatting in it's path ('lazy-loaded' in previous implementation) are now expanded too.
    **Fix:** Use ``!include-raw-escape:`` for them instead.
    See changes in these tests for examples:

    * `lazy-load-jobs-multi001.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/lazy-load-jobs-multi001.yaml>`_
    * `lazy-load-jobs-multi002.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/lazy-load-jobs-multi002.yaml>`_
    * `lazy-load-jobs001.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/lazy-load-jobs001.yaml>`_

  - Parameters with template value using themselves were substituted as is. For example: ``timer: '{timer}'`` was expanded to ``{timer}``.
    Now it leads to recursive parameter error.
    See changes in this test for example:

    * `parameter_name_reuse_default.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/error_fixtures/parameter_name_reuse_default.yaml>`_
    * `parameter_name_reuse_default.xml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/parameter_name_reuse_default.xml>`_
    * `parameter_name_reuse_default.error <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/error_fixtures/parameter_name_reuse_default.error>`_

  - When job group includes a job which was never declared, it was just ignored. Now it fails: job is missing.
    See changes in this test for example:

    * `job_group_includes_missing_job.yaml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/error_fixtures/job_group_includes_missing_job.yaml>`_
    * `job_group_includes_missing_job.xml <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/job_fixtures/job_group_includes_missing_job.xml>`_
    * `job_group_includes_missing_job.error <https://review.opendev.org/c/jjb/jenkins-job-builder/+/871965/5/tests/yamlparser/error_fixtures/job_group_includes_missing_job.error>`_

Features added
~~~~~~~~~~~~~~

* Error handling is improved: now JJB shows tracebacks with error locations
  See these `tests <https://opendev.org/jjb/jenkins-job-builder/src/branch/master/tests/yamlparser/error_fixtures>`_ for examples.
* Added support for Python 3.9 and 3.10.
* Added configuration for Suppress SCM Triggering (by Piotr Falkowski).
* Added discord-notifier publisher (by Ettore Leandro Tognoli).

Bugs fixed
~~~~~~~~~~

* ``--enabled-only`` option when updating jobs (by Thomas Bechtold).
* Default value does not propertly unescape curly braces
  (`Story 2006270 <https://storyboard.openstack.org/#!/story/2006270>`_).
* Different behaviour on defaults list and inline variables for Jenkins Job Builder
  (`Story 2008510 <https://storyboard.openstack.org/#!/story/2008510>`_).
* TypeError: argument of type ``Jinja2Loader`` is not iterable
  (`Story 2010428 <https://storyboard.openstack.org/#!/story/2010428>`_).
* ``yaml.load`` without ``Loader=`` is deprecated
  (`Story 2006725 <https://storyboard.openstack.org/#!/story/2006725>`_).
* ``j2-yaml`` is not allowed inside macro body
  (`Story 2010534 <https://storyboard.openstack.org/#!/story/2010534>`_).
