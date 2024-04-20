import argparse
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='VCS')
    subparsers = parser.add_subparsers()

    subparsers.add_parser('init', help='Init repo in current directory')
    subparsers.add_parser('status', help='Show file statuses')
    subparsers.add_parser('log', help='Show commits log')

    add_parser = subparsers.add_parser('add', help='Start tracking file')
    add_parser.add_argument('files', nargs='+', help='List of files to add')

    commit_parser = subparsers.add_parser('commit', help='Commit files (send to the server)')
    commit_parser.add_argument('message', help='Commit message')

    reset_parser = subparsers.add_parser('reset', help='Reset repository state to specified commit')
    reset_parser.add_argument('hash', help='Commit hash')

    args = parser.parse_args()

    print(args)