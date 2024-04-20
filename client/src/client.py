from pathlib import Path
import shutil

import serverstub as server

HIDDEN_DIR_NAME = ".vcs"
TRACKED_FILE_NAME = ".tracked"
CHANGED_FILE_NAME = ".changed"
HEAD_HASH = ".head"


def _find_metadir() -> Path | None:
    cur_dir = Path.cwd()
    candidate = cur_dir / HIDDEN_DIR_NAME
    if candidate.exists():
        return candidate
    for parent in cur_dir.parents:
        candidate = parent / HIDDEN_DIR_NAME
        if candidate.exists():
            return candidate


def _add_file_to_tracked(metadir: Path, rel_path: Path):
    tracked_file = metadir / TRACKED_FILE_NAME
    with open(tracked_file, "a") as out:
        out.write(str(rel_path) + '\n')
    print("Added:", rel_path)


def _get_head_hash() -> str | None:
    hash_head_file = _find_metadir() / HEAD_HASH
    with open(hash_head_file, "r") as inp:
        line = inp.readline()
    return line


def init(args):
    existing_metadir = _find_metadir()
    if existing_metadir is not None:
        print("Repositories could not be nested:", existing_metadir)
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

    tracked_file = hidden_dir / HEAD_HASH
    tracked_file.touch()
    print('Local repository initialized successfully')

    ok = server.init()
    if ok:
        print('Remote repository initialized successfully')
    else:
        print('Failed to initialize remote repository')


def add(args):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return

    root_dir = metadir.parent
    relative_paths = args.files
    for rel_path in relative_paths:
        path = root_dir / rel_path
        if not path.exists():
            print(f"File {path} not exists")
            continue

        if path.is_dir():
            for nested_file in path.rglob('*'):
                _add_file_to_tracked(metadir, nested_file.relative_to(root_dir))
        elif path.is_file():
            _add_file_to_tracked(metadir, path.relative_to(root_dir))


def status(args):
    pass


def commit(args):
    pass


def reset(args):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return

    # TODO: prompt user about local changes deletion
    hash_to_reset = args.hash
    snapshot_path = server.reset(hash_to_reset)
    if snapshot_path is None:
        print("Failed to reset: no snapshot path returned")
        return

    snapshot_path = Path(snapshot_path)
    if not snapshot_path.exists():
        print("Failed to reset: snapshot path not exists")
        return

    root_dir = metadir.parent
    for path in root_dir.glob("*"):
        if path.is_dir() and path.name != HIDDEN_DIR_NAME:
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        # TODO: add symlinks handling?

    shutil.copytree(snapshot_path, root_dir, dirs_exist_ok=True)
    print("Reset completed!")


def log(args):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return

    commits = server.log()
    if commits is None:
        print("Failed to receive commit logs from server")
        return

    if not commits:
        print("No commits added yet")
        return

    head_hash = _get_head_hash()
    if head_hash is None or not head_hash.strip():
        print("Alert: Head is not defined")
    else:
        head_hash = head_hash.strip()

    print("Commit log:")
    for hsh, message in commits:
        pointer = "->" if hsh == head_hash else "  "
        print(f'{pointer} {hsh}: "{message}"')
