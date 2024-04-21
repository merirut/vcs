import shutil
from pathlib import Path

import serverstub as server
from hash_utils import calculate_hash_for_file, calculate_hash_for_files

HIDDEN_DIR_NAME = ".vcs"
TRACKED_FILE_NAME = ".tracked"
CHANGED_FILE_NAME = ".changes"
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


def _list_traversal_from(path: Path) -> list[Path]:
    return list(filter(lambda nested_path: nested_path.is_file() and HIDDEN_DIR_NAME not in nested_path.parts,
                       path.rglob('*')))


def _get_head_hash() -> str | None:
    hash_head_file = _find_metadir() / HEAD_HASH
    with open(hash_head_file, "r") as inp:
        line = inp.readline()
    return line


def add(args):
    relative_paths = args.files
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")

    root_dir = metadir.parent
    for rel_path in relative_paths:
        abs_path = root_dir / rel_path

        if not abs_path.exists():
            print(f"File {abs_path} not exists")
            continue

        if HIDDEN_DIR_NAME in abs_path.parts:
            print(f"File {abs_path} cannot be inside metadir")
            continue

        if abs_path.is_dir():
            for nested_file in _list_traversal_from(abs_path):
                _add_file_to_tracked(metadir, nested_file.relative_to(abs_path))

        elif abs_path.is_file():
            _add_file_to_tracked(metadir, abs_path)


def _add_file_to_tracked(metadir: Path, rel_path_from_root: Path):
    tracked_file = metadir / TRACKED_FILE_NAME
    tracked_rel_paths = _read_tracked(metadir).keys()
    if str(rel_path_from_root) not in tracked_rel_paths:
        with open(tracked_file, "a") as file:
            file.write(str(rel_path_from_root) + " 0\n")
            print("Added: ", rel_path_from_root)
    else:
        print(rel_path_from_root, "is already tracking")


def init(args):
    existing_metadir = _find_metadir()
    if existing_metadir is not None:
        print("Repositories could not be nested:", existing_metadir, "\n")
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

    head_file = hidden_dir / HEAD_HASH
    head_file.touch()
    with open(head_file, "w") as file:
        file.write("0")

    print("Local repository initialized successfully")

    ok = server.init()
    if ok:
        print("Remote repository initialized successfully")
    else:
        print("Failed to initialize remote repository")


def _read_tracked(metadir: Path, relative: bool = True) -> dict[str, str]:
    tracked_file = metadir / TRACKED_FILE_NAME
    tracked_shas_from_prev_commit = {}
    root_dir = metadir.parent
    with open(tracked_file, "r") as file:
        lines = file.read().splitlines()
        for line in lines:
            rel_path, sha = line.split(" ")
            path = rel_path if relative else root_dir / rel_path
            tracked_shas_from_prev_commit[path] = sha
    return tracked_shas_from_prev_commit

def status(args):
    added_files, modified_files, deleted_files = _calculate_status()
    if not added_files and not modified_files and not deleted_files:
        print("Nothing changed")
        return

    for file in added_files:
        print("Added:", file)

    for file in modified_files:
        print("Modified:", file)

    for file in deleted_files:
        print("Deleted:", file)


def _calculate_status():
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return

    root_dir = metadir.parent
    original_tracked = _read_tracked(metadir)
    sha_by_rel_path = original_tracked.copy()
    all_files = _list_traversal_from(root_dir)
    modified_files = []
    added_files = []
    for abs_file in all_files:
        rel_file = str(abs_file.relative_to(root_dir))
        if rel_file in sha_by_rel_path:
            fresh_sha = calculate_hash_for_file(abs_file)
            sha_from_last_commit = sha_by_rel_path.pop(rel_file)
            if sha_from_last_commit == "0":  # added first time, not committed yet
                added_files.append(rel_file)
            elif sha_from_last_commit != fresh_sha:
                modified_files.append(rel_file)

    tracked_file = metadir / TRACKED_FILE_NAME

    deleted_files = list(filter(lambda p: sha_by_rel_path[p] != '0', sha_by_rel_path.keys()))

    files_to_delete_from_tracked = list(filter(lambda p: sha_by_rel_path[p] == '0', sha_by_rel_path.keys()))
    if files_to_delete_from_tracked:
        with open(tracked_file, "w") as rel_file:
            for rel_path, sha in original_tracked.items():
                if rel_path not in files_to_delete_from_tracked:
                    rel_file.write(f"{rel_path} {sha}\n")

    return added_files, modified_files, deleted_files


def _is_file_tracked(metadir, rel_path):
    tracked_path = metadir / TRACKED_FILE_NAME
    with open(tracked_path, "r") as tracked_file:
        return str(rel_path) in tracked_file.read().splitlines()


def commit(args):
    message = args.message
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return
    root_dir = metadir.parent
    head_hash = _get_head_hash()
    # generate .changes
    changes_generated = _generate_changes_file(metadir)
    if not changes_generated:
        print("There is nothing to commit!")
        return
    # calculate new commit hash

    new_hash, sha_by_abs_path = calculate_hash_for_files(_read_tracked(metadir, relative=False))
    # send to server
    ok = server.commit(message, str(root_dir), head_hash, new_hash)
    if not ok:
        print("Failed to commit: something went wrong!")
        return
    print("Committed successfully!")
    # update shas in .tracked
    _override_tracked(metadir, sha_by_abs_path)
    # update head
    _override_head(metadir, new_hash)
    # clear changes
    _clear_changes(metadir)


def _override_tracked(metadir, sha_by_abs_path):
    tracked_file = metadir / TRACKED_FILE_NAME
    root_dir = metadir.parent
    with open(tracked_file, "w") as file:
        for abs_path, sha in sha_by_abs_path.items():
            file.write(f"{Path(abs_path).relative_to(root_dir)} {sha}\n")


def _override_head(metadir, new_head_hash):
    head_file = metadir / HEAD_HASH
    with open(head_file, "w") as file:
        file.write(new_head_hash)


def _clear_changes(metadir):
    changes_file = metadir / CHANGED_FILE_NAME
    open(changes_file, 'w').close()


def _generate_changes_file(metadir: Path) -> bool:
    added_files, modified_files, deleted_files = _calculate_status()
    if not added_files and not modified_files and not deleted_files:
        return False

    changes_file = metadir / CHANGED_FILE_NAME
    with open(changes_file, "w") as file:
        for f in added_files:
            file.write(f"a {f}\n")

        for f in modified_files:
            file.write(f"m {f}\n")

        for f in deleted_files:
            file.write(f"d {f}\n")
    return True

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
    for hsh, timestamp, message in commits:
        pointer = "->" if hsh == head_hash else "  "
        print(f'{pointer} {hsh}: {timestamp} : {message}')
