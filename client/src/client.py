import shutil
from pathlib import Path

import serverstub as server
from create_changes import calculate_hash

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


def _get_head_hash() -> str | None:
    hash_head_file = _find_metadir() / HEAD_HASH
    with open(hash_head_file, "r") as inp:
        line = inp.readline()
    return line


def add(args):
    # TODO: add file to tracked with sha = 0
    return _apply_tracked_operation_to_files(args, _add_dir_to_tracked, _add_file_to_tracked, _add_dir_to_tracked)


def remove(args):
    return _apply_tracked_operation_to_files(args, _delete_dir_from_tracked, _delete_file_from_tracked,
                                             _delete_dir_from_tracked)


def _apply_tracked_operation_to_files(args, function_applied_to_dir, function_applied_to_file,
                                      function_nothing_specified):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return
    root_dir = metadir.parent
    relative_paths = args.files
    if not args.files:
        function_nothing_specified(metadir, root_dir)
    for rel_path in relative_paths:
        if _is_inside_metadir(rel_path):
            print(f"{rel_path} - Files in {HIDDEN_DIR_NAME} cannot be altered!")
            continue
        path = root_dir / rel_path
        if not path.exists():
            print(f"Destination {rel_path} does not exist")
            continue
        if path.is_dir():
            function_applied_to_dir(metadir, path)
        elif path.is_file():
            function_applied_to_file(metadir, path)


def _is_inside_metadir(path):
    return HIDDEN_DIR_NAME in path.parts


def _add_file_to_tracked(metadir: Path, path: Path):
    rel_path = path.relative_to(metadir.parent)
    tracked_file = metadir / TRACKED_FILE_NAME
    with open(tracked_file, "ra") as file:
        lines = file.read().splitlines()
        if rel_path not in lines:
            file.write(str(rel_path) + "\n")
            print("Added: ", rel_path)
        else:
            print(rel_path, "is already tracking")


def _delete_file_from_tracked(metadir, path):
    rel_path = path.relative_to(metadir.parent)
    tracked_file = metadir / TRACKED_FILE_NAME
    with open(tracked_file, "rw") as file:
        filtered = filter(lambda line: line != rel_path, file.readlines())
        file.writelines(filtered)


def _add_dir_to_tracked(metadir: Path, path: Path):
    return _traverse_from(metadir, path, _add_file_to_tracked)


def _delete_dir_from_tracked(metadir, path):
    return _traverse_from(metadir, path, _delete_file_from_tracked)


def _traverse_from(metadir, path, function_applied_to_file):
    for nested_path in path.rglob('*'):
        if nested_path.is_file() and HIDDEN_DIR_NAME not in nested_path.parts:
            print("Trav", nested_path)
            function_applied_to_file(metadir, nested_path)


def _list_traversal_from(path):
    return filter(lambda nested_path: nested_path.is_file() and HIDDEN_DIR_NAME not in nested_path.parts,
                  path.rglob('*'))


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


def _extract_tracked_shas(metadir):
    tracked_file = metadir / TRACKED_FILE_NAME
    tracked_shas_from_prev_commit = {}
    with open(tracked_file, "r") as file:
        lines = file.read().splitlines()
        for line in lines:
            rel_path, sha = line.split(" ")
            tracked_shas_from_prev_commit[rel_path] = sha
    return tracked_shas_from_prev_commit


def status(args):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return

    root_dir = metadir.parent
    sha_by_rel_path = _extract_tracked_shas(metadir)
    all_files = _list_traversal_from(root_dir)
    modified_files = []
    added_files = []
    for file in all_files:
        if file in sha_by_rel_path:
            fresh_sha = calculate_hash(file)
            sha_from_last_commit = sha_by_rel_path.pop(file)
            if sha_from_last_commit == "0":  # added first time, not committed yet
                added_files.append(file)
            elif sha_from_last_commit != fresh_sha:
                modified_files.append(file)
    deleted_files = sha_by_rel_path.keys()

    if not added_files and not modified_files and not deleted_files:
        print("Nothing changed")
        return

    for file in added_files:
        print("Added:", file)

    for file in modified_files:
        print("Modified:", file)

    for file in deleted_files:
        print("Deleted:", file)


def _is_in_tracked(metadir, rel_path):
    tracked_path = metadir / TRACKED_FILE_NAME
    with open(tracked_path, "r") as tracked_file:
        return str(rel_path) in tracked_file.read().splitlines()


def commit(message):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return
    head_hash = _get_head_hash()
    # generate_changes(metadir)
    # new_hash = _generate_new_hash()
    ok = server.commit(message, str(metadir.parent), head_hash, new_hash)
    if not ok:
        print("Something went wrong!")


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
