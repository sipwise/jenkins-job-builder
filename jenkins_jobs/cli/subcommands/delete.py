
def parse(subparser, parents):
    parser_delete = subparser.add_parser('delete', parents=parents)
    parser_delete.add_argument('name', help='name of job', nargs='+')
    parser_delete.add_argument('-p', '--path', default=None,
                               help='colon-separated list of paths to'
                                    ' YAML files or directories')
