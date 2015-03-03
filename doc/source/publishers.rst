.. _publishers:

Publishers
==========

When writing a publisher macro, it is important to keep in mind that Jenkins
uses Ant's `SCP Task <https://ant.apache.org/manual/Tasks/scp.html>`_ via the
Jenkins `SCP Plugin <https://wiki.jenkins-ci.org/display/JENKINS/SCP+plugin>`_
which relies on `FileSet <https://ant.apache.org/manual/Types/fileset.html>`_
and `DirSet <https://ant.apache.org/manual/Types/dirset.html>`_ patterns.
The relevant piece of documentation is excerpted below:

    Source points to files which will be uploaded. You can use ant includes
    syntax, eg. ``folder/dist/*.jar``. Path is constructed from workspace
    root. Note that you cannot point files outside the workspace directory.
    For example providing: ``../myfile.txt`` won't work... Destination points
    to destination folder on remote site. It will be created if doesn't exists
    and relative to root repository path. You can define multiple blocks of
    source/destination pairs.

This means that absolute paths, e.g., ``/var/log/**`` will not work and will fail
to compile. All paths need to be relative to the directory that the publisher
runs and the paths have to be contained inside of that directory. The relative
working directory is usually::

    /home/jenkins/workspace/${JOB_NAME}

.. automodule:: publishers
   :members:
