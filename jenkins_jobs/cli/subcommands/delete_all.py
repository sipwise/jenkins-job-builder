
def parse(subparser, parents):
    subparser.add_parser('delete-all',
                         help='delete *ALL* jobs from Jenkins server, '
                         'including those not managed by Jenkins Job '
                         'Builder.')
