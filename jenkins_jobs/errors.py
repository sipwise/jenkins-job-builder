"""Exception classes for jenkins_jobs errors"""

import inspect


def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            (hasattr(arg, "__getitem__") or
             hasattr(arg, "__iter__")))


class JenkinsJobsException(Exception):
    pass


class ModuleError(JenkinsJobsException):

    def get_module_name(self):
        frame = inspect.currentframe()
        co_name = frame.f_code.co_name
        while frame and co_name != 'run':
            if co_name == 'dispatch':
                data = frame.f_locals
                module_name = "%s.%s" % (data['component_type'], data['name'])
                break
            frame = frame.f_back
            co_name = frame.f_code.co_name

        return module_name


class InvalidAttributeError(ModuleError):

    def __init__(self, attribute_name, value, valid_values=None):
        message = "'{0}' is an invalid value for attribute {1}.{2}".format(
            value, self.get_module_name(), attribute_name)

        if is_sequence(valid_values):
            message += "\nValid values include: {0}".format(
                ', '.join("'{0}'".format(value)
                          for value in valid_values))

        super(InvalidAttributeError, self).__init__(message)


class MissingAttributeError(ModuleError):

    def __init__(self, missing_attribute):
        if is_sequence(missing_attribute):
            message = "One of {0} must be present in {1}".format(
                ', '.join("'{0}'".format(value)
                          for value in missing_attribute),
                self.get_module_name())
        else:
            message = "Missing {0} from an instance of {1}".format(
                missing_attribute, self.get_module_name())

        super(MissingAttributeError, self).__init__(message)


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
