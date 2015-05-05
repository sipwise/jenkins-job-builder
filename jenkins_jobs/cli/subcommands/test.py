import sys


def parse(subparser, parents):
    parser_test = subparser.add_parser('test', parents=parents)
    parser_test.add_argument('path', help='colon-separated list of paths to'
                                          ' YAML files or directories',
                             nargs='?', default=sys.stdin)
    parser_test.add_argument('-p', dest='plugins_info_path', default=None,
                             help='path to plugin info YAML file')
    parser_test.add_argument('-o', dest='output_dir', default=sys.stdout,
                             help='path to output XML')
    parser_test.add_argument('name', help='name(s) of job(s)', nargs='*')
