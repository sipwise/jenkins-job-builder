README
======

Jenkins Job Builder takes simple descriptions of Jenkins_ jobs in YAML_ or JSON_
format and uses them to configure Jenkins. You can keep your job descriptions in
human readable text format in a version control system to make changes and
auditing easier. It also has a flexible template system, so creating many
similarly configured jobs is easy.

To install::

    $ pip install --user jenkins-job-builder

Online documentation:

* https://jenkins-job-builder.readthedocs.io/en/latest/

Developers
----------
Bug report:

* https://storyboard.openstack.org/#!/project/723

Repository:

* https://opendev.org/jjb/jenkins-job-builder

Cloning::

    git clone https://opendev.org/jjb/jenkins-job-builder.git

Install pre-commit from https://pre-commit.com/#intro in order to run some
minimal testing on your commits.

A virtual environment is recommended for development.  For example, Jenkins
Job Builder may be installed from the top level directory::

    $ virtualenv .venv
    $ source .venv/bin/activate
    $ pip install -r test-requirements.txt -e .

Patches are submitted via Gerrit at:

* https://review.opendev.org

Please do not submit GitHub pull requests, they will be automatically closed.

Mailing list:

* https://groups.google.com/forum/#!forum/jenkins-job-builder

IRC:

* ``#openstack-jjb`` on Freenode

More details on how you can contribute is available on our wiki at:

* https://docs.openstack.org/infra/manual/developers.html

Writing a patch
---------------

We ask that all code submissions be pep8_ and pyflakes_ clean.  The
easiest way to do that is to run tox_ before submitting code for
review in Gerrit.  It will run ``pep8`` and ``pyflakes`` in the same
manner as the automated test suite that will run on proposed
patchsets.

When creating new YAML components, please observe the following style
conventions:

* All YAML identifiers (including component names and arguments)
  should be lower-case and multiple word identifiers should use
  hyphens.  E.g., "build-trigger".
* The Python functions that implement components should have the same
  name as the YAML keyword, but should use underscores instead of
  hyphens. E.g., "build_trigger".

This consistency will help users avoid simple mistakes when writing
YAML, as well as developers when matching YAML components to Python
implementation.

Unit Tests
----------

Unit tests have been included and are in the ``tests`` folder. Many unit
tests samples are included as examples in our documentation to ensure that
examples are kept current with existing behaviour. To run the unit tests,
execute the command::

    tox -e py34,py27

* Note: View ``tox.ini`` to run tests on other versions of Python,
  generating the documentation and additionally for any special notes
  on running the test to validate documentation external URLs from behind
  proxies.

Installing without setup.py
---------------------------

For YAML support, you will need libyaml_ installed.

Mac OS X::

    $ brew install libyaml

Then install the required python packages using pip_::

    $ sudo pip install PyYAML python-jenkins

.. _Jenkins: https://jenkins.io/
.. _YAML: https://yaml.org
.. _JSON: http://json.org/
.. _pep8: https://pypi.org/project/pep8
.. _pyflakes: https://pypi.org/project/pyflakes
.. _tox: https://tox.readthedocs.io/en/latest
.. _libyaml: https://pyyaml.org/wiki/LibYAML
.. _pip: https://pypi.org/project/pip
