import os
import hashlib

"""Calculate the sha256 hash of a file."""
def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()

"""Generates a file .changes needed for updating the repo on the server when committing"""
def generate_changes(root_absolute_path):
    vcs_file_path = os.path.join(root_absolute_path, ".vcs")
    if not os.path.exists(vcs_file_path):
        raise Exception(".vcs folder not found. Please initialize vcs first")
    changes = []
    new_file_hashes = {}
    tracked_file_path = os.path.join(vcs_file_path, ".tracked")
    if os.path.exists(tracked_file_path):
        with open(tracked_file_path, "r") as tracked:
            tracked_files_relative_paths = tracked.read().splitlines()

        lastcommit_file_path = os.path.join(vcs_file_path, "lastcommit")
        for relative_path in tracked_files_relative_paths:
            file_path = os.path.join(lastcommit_file_path, relative_path)
            new_file_hashes[file_path] = calculate_hash(file_path)
            
        for relative_path in tracked_files_relative_paths:
            file_path = os.path.join(root_absolute_path, relative_path)

            if file_path not in new_file_hashes:
                changes.append(f"-d {file_path}")
            elif calculate_hash(file_path) != new_file_hashes[file_path]:
                changes.append(f"-m {file_path}")
                del new_file_hashes[file_path]
        for key in new_file_hashes.keys():
        	changes.append(f"-a {file_path}")

    changes_file_path = os.path.join(vcs_file_path, ".changes")
    with open(changes_file_path, "w") as changes_file:
        changes_file.write("\n".join(changes))
   