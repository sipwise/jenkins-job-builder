

def parse(subparser, parents):
    update = subparser.add_parser('update', parents=parents)
    update.add_argument('path', help='colon-separated list of paths to'
                                     ' YAML files or directories')
    update.add_argument('names', help='name(s) of job(s)', nargs='*')
    update.add_argument('--delete-old', help='delete obsolete jobs',
                        action='store_true',
                        dest='delete_old', default=False,)
    update.add_argument('--workers', dest='n_workers', type=int,
                        default=1, help='number of workers to use, 0 '
                        'for autodetection and 1 for just one worker.')
