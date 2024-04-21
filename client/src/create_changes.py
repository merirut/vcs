from pathlib import Path
from client import HIDDEN_DIR_NAME, TRACKED_FILE_NAME, CHANGED_FILE_NAME
import hashlib


# Calculate the sha256 hash of a file.
def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()


# Generates a file .changes needed for updating the repo on the server when committing
def generate_changes(metadir):
    vcs_file_path = metadir / HIDDEN_DIR_NAME
    if not vcs_file_path.exists():
        print(".vcs folder not found. Please initialize vcs first")
        return
    changed = []
    new_file_hashes = {}
    tracked_file_path = vcs_file_path / TRACKED_FILE_NAME
    if tracked_file_path.exists():
        with open(tracked_file_path, "r") as tracked:
            tracked_files_relative_paths = tracked.read().splitlines()
        lastcommit_file_path = vcs_file_path / "lastcommit"

        for relative_path in tracked_files_relative_paths:
            file_path = lastcommit_file_path / relative_path
            new_file_hashes[file_path] = calculate_hash(file_path)

        for relative_path in tracked_files_relative_paths:
            file_path = metadir / relative_path
            if file_path not in new_file_hashes:
                changed.append(f"-d {file_path}")
            elif calculate_hash(file_path) != new_file_hashes[file_path]:
                changed.append(f"-m {file_path}")
                del new_file_hashes[file_path]

        for key in new_file_hashes.keys():
            changed.append(f"-a {key}")

    changed_file_path = vcs_file_path / CHANGED_FILE_NAME
    with open(changed_file_path, "w") as changed_file:
        changed_file.write("\n".join(changed))
