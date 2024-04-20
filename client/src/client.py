from pathlib import Path

import serverstub as server

HIDDEN_DIR_NAME = ".vcs"
TRACKED_FILE_NAME = ".tracked"
CHANGED_FILE_NAME = ".changed"


def init():
    cur_dir = Path.cwd()
    hidden_dir = cur_dir / HIDDEN_DIR_NAME
    if hidden_dir.exists():
        print("Repository in this folder already exists")
        return

    hidden_dir.mkdir()

    changed_file = hidden_dir / CHANGED_FILE_NAME
    changed_file.touch()

    tracked_file = hidden_dir / TRACKED_FILE_NAME
    tracked_file.touch()

    ok = server.init()
    if ok:
        print('Repository initialized successfully')
    else:
        print('Failed to initialize repository')


def status(args):
    pass


def add(args):
    pass


def commit(args):
    pass


def reset(args):
    pass


def log(args):
    pass
