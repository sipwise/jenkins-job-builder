"""Exception classes for jenkins_jobs errors"""


class JenkinsJobsException(Exception):
    pass


class YAMLStructureError(JenkinsJobsException):
    """Raised when the structure of YAML is not as expected."""

    def __init__(self, *args, **kwargs):
        super(YAMLStructureError, self).__init__(*args, **kwargs)
        self._item_name = self._near = self._file_name = None

    def item_name(self, name):
        """Specifies the name of the problematic item."""
        self._item_name = name
        return self

    def near(self, item):
        """Specifies the definition of the problematic item."""
        self._near = item
        return self

    def file_name(self, fname):
        """Specifies the name of file where the problematic item has been
        found."""
        self._file_name = fname
        return self

    def __str__(self):
        msg = []
        if self.message:
            msg.append(self.message)
        if self._item_name:
            msg.append("Item named: '{name}'".format(name=self._item_name))
        if self._file_name:
            msg.append("In file: {file}".format(file=self._file_name))
        if self._near:
            msg.append("Near: {near}".format(near=self._near))
        return '\n  '.join(msg)
