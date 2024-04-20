from pathlib import Path

import serverstub as server

HIDDEN_DIR_NAME = ".vcs"
TRACKED_FILE_NAME = ".tracked"
CHANGED_FILE_NAME = ".changed"


def _find_metadir() -> Path | None:
    cur_dir = Path.cwd()
    for parent in cur_dir.parents:
        candidate = parent / HIDDEN_DIR_NAME
        if candidate.exists():
            return candidate


def _add_file_to_tracked(metadir: Path, rel_path: Path):
    tracked_file = metadir / TRACKED_FILE_NAME
    with open(tracked_file, "a") as out:
        out.write(str(tracked_file) + '\n')
    print("Added:", rel_path)


def init():
    existing_metadir = _find_metadir()

    if existing_metadir is not None:
        print("Repository could not be nested:", existing_metadir)
        return

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


def add(args):
    relative_paths = args.files
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")

    for rel_path in relative_paths:
        path = metadir / rel_path
        if not path.exists():
            print(f"File {path} not exists")
            continue

        if path.is_dir():
            for nested_file in path.rglob('*'):
                _add_file_to_tracked(nested_file.relative_to(path))
        elif path.is_file():
            _add_file_to_tracked(path)


def status(args):
    pass


def commit(args):
    pass


def reset(args):
    pass


def log(args):
    pass
