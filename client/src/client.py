import colorama
from create_changes import calculate_hash, generate_changes
from pathlib import Path
from datetime import datetime
import shutil
import os

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


def add(args):
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
    return _traverse_file_tree_from_dir(metadir, path, _add_file_to_tracked)


def _delete_dir_from_tracked(metadir, path):
    return _traverse_file_tree_from_dir(metadir, path, _delete_file_from_tracked)


def _traverse_file_tree_from_dir(metadir, path, function_applied_to_file):
    for nested_file in path.rglob('*'):
        function_applied_to_file(metadir, nested_file)


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

    tracked_file = hidden_dir / HEAD_HASH
    tracked_file.touch()
    print("Local repository initialized successfully")

    ok = server.init()
    if ok:
        print("Remote repository initialized successfully")
    else:
        print("Failed to initialize remote repository")


def status(args):
    colorama.init()
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return
    _traverse_file_tree_from_dir(metadir, metadir.parent, _status_see_if_file_added_or_modified)
    _traverse_file_tree_from_dir(metadir, metadir / "lastcommit", _status_see_if_file_deleted)


def _status_see_if_file_added_or_modified(metadir, nested_file):
    rel_path = nested_file.relative_to(metadir.parent)
    lastcommit_file = metadir / "lastcommit" / rel_path
    is_in_tracked = _is_in_tracked(metadir, rel_path)
    if not lastcommit_file.exists():
        print(colorama.Fore.GREEN + "Tracked" if is_in_tracked else "Untracked" +
            f" - {rel_path} - added and last modified at {datetime.fromtimestamp(nested_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    elif nested_file.stat().st_mtime != lastcommit_file.stat().st_mtime:
        print(colorama.Fore.GREEN + "Tracked" if is_in_tracked else "Untracked" +
            f" - {rel_path} - last modified at {datetime.fromtimestamp(nested_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")


def _status_see_if_file_deleted(metadir, nested_file):
    rel_path = nested_file.relative_to(metadir / "lastcommit")
    local_file = metadir.parent / rel_path
    is_in_tracked = _is_in_tracked(metadir, rel_path)
    if not local_file.exists():
        print(colorama.Fore.RED + "Tracked" if is_in_tracked else "Untracked" + f" - {rel_path} - deleted")


def _is_in_tracked(metadir, path):
    rel_path = path.relative_to(metadir.parent)
    tracked_file = metadir / TRACKED_FILE_NAME
    with open(tracked_file, "r") as file:
        for line in file.readlines():
            if line.strip() == str(rel_path):
                return 1
    return 0


def commit(message):
    metadir = _find_metadir()
    if metadir is None:
        print(HIDDEN_DIR_NAME, "directory not found. Is repository initialized?")
        return
    generate_changes(metadir)
    head_hash = _get_head_hash()
    new_hash = _generate_new_hash()
    success = server.commit(message, str(metadir.parent), head_hash, new_hash)

    if not success:
        print("Something went wrong!")



# Something along these lines - I'm too tired for this rn
# def generate_new_hash(directory):
#     # Create a new SHA-1 hash object
#     sha1 = hashlib.sha1()
#
#     # Iterate over all files and directories in the directory
#     for root, dirs, files in os.walk(directory):
#         # Sort the directories and files for consistency
#         dirs.sort()
#         files.sort()
#
#         # Update the hash with the relative path and content of each file
#         for file in files:
#             file_path = os.path.join(root, file)
#             with open(file_path, 'rb') as f:
#                 # Update the hash with the relative path
#                 sha1.update(os.path.relpath(file_path, directory).encode('utf-8'))
#
#                 # Update the hash with the content of the file
#                 sha1.update(f.read())
#
#     # Return the hexadecimal representation of the hash digest
#     return sha1.hexdigest()

def _get_head_hash() -> str | None:
    hash_head_file = _find_metadir() / HEAD_HASH
    with open(hash_head_file, "r") as inp:
        line = inp.readline()
    return line


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
