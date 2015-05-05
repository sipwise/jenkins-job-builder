import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseSubCommand(object):
    """Base class for Jenkins Job Builder subcommands, intended to allow
    subcommands to be loaded as stevedore extensions by third party users.
    """
    def __init__(self):
        pass

    @abc.abstractmethod
    def parse_args(self, subparsers, recursive_parser):
        """Define subcommand arguments.

        :param subparsers
          A sub parser object. Implementations of this method should
          create a new subcommand parser by calling
            parser = subparsers.add_parser('command-name', ...)
          This will return a new ArgumentParser object; all other arguments to
          this method will be passed to the argparse.ArgumentParser constructor
          for the returned object.
        """

    @abc.abstractmethod
    def execute(self, config):
        """Perform wonderfual maricals.

        :param config
          JJBConfig object containing final configuration from config files,
          command line arguments, and environment variables.
        """

    @staticmethod
    def parse_option_recursive(parser):
        """Add '--recursive' argument to given parser.
        """
        parser.add_argument('-r', '--recursive',
                            action='store_true',
                            dest='recursive',
                            default=False,
                            help='look for yaml files recursively')

    @staticmethod
    def parse_option_exclude(parser):
        """Add '--exclude' argument to given parser.
        """
        parser.add_argument('-x',
                            '--exclude',
                            dest='exclude',
                            action='append',
                            default=[],
                            help='''paths to exclude when using recursive
                            search, uses standard globbing.''')
