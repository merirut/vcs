import argparse

from client import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VCS')
    subparsers = parser.add_subparsers()

    init_parser = subparsers.add_parser('init', help='Init repo in current directory')
    init_parser.set_defaults(func=init)

    status_parser = subparsers.add_parser('status', help='Show file statuses')
    status_parser.set_defaults(func=status)

    log_parser = subparsers.add_parser('log', help='Show commits log')
    log_parser.set_defaults(func=log)

    add_parser = subparsers.add_parser('add', help='Start tracking files')
    add_parser.add_argument('files', nargs='*',
                            help='List of files to add. If no files specified adds all from root directory.')
    add_parser.set_defaults(func=add)

    commit_parser = subparsers.add_parser('commit', help='Commit files (send to the server)')
    commit_parser.add_argument('message', help='Commit message')
    commit_parser.set_defaults(func=commit)

    reset_parser = subparsers.add_parser('reset', help='Reset repository state to specified commit')
    reset_parser.add_argument('hash', help='Commit hash')
    reset_parser.set_defaults(func=reset)

    args = parser.parse_args()
    args.func(args)
