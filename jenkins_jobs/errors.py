"""Exception classes for jenkins_jobs errors"""


class JenkinsJobsException(Exception):
    pass


class InvalidAttributeError(JenkinsJobsException):

    def __init__(self, attribute_name, value, module_name, valid_values=None):
        message = "'{1}' invalid value for atribute {2}.{0}".format(
            attribute_name, value, module_name)

        if hasattr(valid_values, "__iter__"):
            message += "\nValid values include: {0}".format(
                ', '.join("'{0}'".format(value)
                          for value in valid_values))

        super(InvalidAttributeError, self).__init__(message)


class MissingAttributeError(JenkinsJobsException):

    def __init__(self, missing_attribute, module_name):
        if hasattr(missing_attribute, '__iter__'):
            message = "One of {0} must be present in {1}".format(
                ', '.join("'{0}'".format(value)
                          for value in missing_attribute),
                module_name)
        else:
            message = "Missing {0} from an instance of {1}".format(
                missing_attribute, module_name)
        super(MissingAttributeError, self).__init__(message)


class YAMLFormatError(JenkinsJobsException):
    pass
