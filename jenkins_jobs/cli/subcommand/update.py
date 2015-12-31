
import jenkins_jobs.cli.subcommand.base as base


class UpdateSubCommand(base.BaseSubCommand):
    def parse_args(self, subparser):
        update = subparser.add_parser('update')

        self.parse_option_recursive(update)
        self.parse_option_exclude(update)

        update.add_argument('path',
                            help='''colon-separated list of paths to YAML files
                            or directories''')
        update.add_argument('names',
                            help='name(s) of job(s)', nargs='*')
        update.add_argument('--delete-old',
                            help='delete obsolete jobs',
                            action='store_true',
                            dest='delete_old',
                            default=False,)
        update.add_argument('--workers',
                            help='''number of workers to use, 0 for
                            autodetection and 1 for just one worker.''',
                            dest='n_workers',
                            type=int,
                            default=1)

    def execute(self, config):
        raise NotImplementedError
