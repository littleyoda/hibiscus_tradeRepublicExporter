# Based on https://github.com/pytr-org/pytr/blob/master/pytr/main.py

import argparse
import asyncio
import signal
from datetime import datetime, timedelta
from pathlib import Path

from pytr.account import login
from pytr.utils import get_logger 
from hibiscusexport import HIBISCUS


def get_main_parser():
    def formatter(prog):
        return argparse.HelpFormatter(prog, max_help_position=25)

    parser = argparse.ArgumentParser(
        formatter_class=formatter,
        description='Use "%(prog)s command_name --help" to get detailed help to a specific command',
    )
    for grp in parser._action_groups:
        if grp.title == 'options':
            grp.title = 'Options'
        elif grp.title == 'positional arguments':
            grp.title = 'Commands'

    parser.add_argument(
        '-v',
        '--verbosity',
        help='Set verbosity level (default: info)',
        choices=['warning', 'info', 'debug'],
        default='info',
    )
    parser.add_argument('-V', '--version', help='Print version information and quit', action='store_true')
    parser_cmd = parser.add_subparsers(help='Desired action to perform', dest='command')

    # help
    parser_cmd.add_parser('help', help='Print this help message', description='Print help message', add_help=False)

    # Create parent subparser with common login arguments
    parser_login_args = argparse.ArgumentParser(add_help=False)
    parser_login_args.add_argument('--applogin', help='Use app login instead of  web login', action='store_true')
    parser_login_args.add_argument('-n', '--phone_no', help='TradeRepublic phone number (international format)')
    parser_login_args.add_argument('-p', '--pin', help='TradeRepublic pin')

    # login
    info = (
        'Check if credentials file exists. If not create it and ask for input. Try to login.'
        + ' Ask for device reset if needed'
    )
    parser_cmd.add_parser(
        'login',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parser_login_args],
        help=info,
        description=info,
    )

    info = (
        'Create a xml-file which can be imported to hibiscus.'
    )
    parser_dl_docs = parser_cmd.add_parser(
        'hibiscus',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        parents=[parser_login_args],
        help=info,
        description=info,
    )

    parser_dl_docs.add_argument('output', help='Output directory', metavar='PATH', type=Path)
    parser_dl_docs.add_argument(
        '--last-days', help='Number of last days to include (use 0 get all days)', metavar='DAYS', default=0, type=int
    )
    parser_dl_docs.add_argument('--save-details', help='Save each transaction as json', action='store_true')
    parser_dl_docs.add_argument('--include-pending', help='Incl. Pending Transactions', action='store_true')
    return parser


def exit_gracefully(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in input when CTRL+C is pressed, and our signal handler is not re-entrant
    global original_sigint
    signal.signal(signal.SIGINT, original_sigint)

    try:
        if input('\nReally quit? (y/n)> ').lower().startswith('y'):
            exit(1)

    except KeyboardInterrupt:
        print('Ok ok, quitting')
        exit(1)

    # restore the exit gracefully handler here
    signal.signal(signal.SIGINT, exit_gracefully)


def main():
    global original_sigint
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)

    parser = get_main_parser()
    args = parser.parse_args()
    log = get_logger(__name__, args.verbosity)
    log.setLevel(args.verbosity.upper())
    log.debug('logging is set to debug')

    if args.command == 'login':
        login(phone_no=args.phone_no, pin=args.pin, web=not args.applogin)

    elif args.command == 'hibiscus':
        if args.last_days == 0:
            since_timestamp = 0
        else:
           since_timestamp = (datetime.now().astimezone() - timedelta(days=args.last_days)).timestamp()
        dl = HIBISCUS(
            login(phone_no=args.phone_no, pin=args.pin, web=not args.applogin),
            args.output,
            since_timestamp=since_timestamp,
            include_pending=args.include_pending,
            save_transcations=args.save_details
        )   
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            asyncio.run(dl.dl_loop())
        except KeyboardInterrupt:
            pass   
   #     asyncio.get_event_loop().run_until_complete(dl.dl_loop())
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
