
import argparse

import jenkins_jobs.version


def version():
    return "Jenkins Job Builder version: %s" % \
        jenkins_jobs.version.version_info.version_string()


def parse(subparser, parents):
    subparser.add_argument('--conf', dest='conf', help='configuration file')
    subparser.add_argument('-l', '--log_level', dest='log_level',
                           default='info',
                           help="log level (default: %(default)s)")
    subparser.add_argument(
        '--ignore-cache', action='store_true',
        dest='ignore_cache', default=False,
        help='ignore the cache and update the jobs anyhow (that will only '
             'flush the specified jobs cache)')
    subparser.add_argument(
        '--flush-cache', action='store_true', dest='flush_cache',
        default=False, help='flush all the cache entries before updating')
    subparser.add_argument('--version', dest='version', action='version',
                           version=version(),
                           help='show version')
    subparser.add_argument(
        '--allow-empty-variables', action='store_true',
        dest='allow_empty_variables', default=None,
        help='Don\'t fail if any of the variables inside any string are not '
        'defined, replace with empty string instead')

    recursive_parser = argparse.ArgumentParser(add_help=False)
    recursive_parser.add_argument('-r', '--recursive', action='store_true',
                                  dest='recursive', default=False,
                                  help='look for yaml files recursively')
    recursive_parser.add_argument('-x', '--exclude', dest='exclude',
                                  action='append', default=[],
                                  help='paths to exclude when using recursive'
                                       ' search, uses standard globbing.')

    return subparser, recursive_parser
