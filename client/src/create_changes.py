# from pathlib import Path
# from client import HIDDEN_DIR_NAME, TRACKED_FILE_NAME, CHANGED_FILE_NAME
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

# Generates a file .changes needed for updating the repo on the server when committing
# def generate_changes(metadir):
#     vcs_file_path = metadir / HIDDEN_DIR_NAME
#     if not vcs_file_path.exists():
#         print(".vcs folder not found. Please initialize vcs first")
#         return
#     changed = []
#     new_file_hashes = {}
#     tracked_file_path = vcs_file_path / TRACKED_FILE_NAME
#     if tracked_file_path.exists():
#         with open(tracked_file_path, "r") as tracked:
#             tracked_files_relative_paths = tracked.read().splitlines()
#         lastcommit_file_path = vcs_file_path / "lastcommit"
#
#         for tracked_file in tracked_files_relative_paths:
#             file_path = lastcommit_file_path / tracked_file
#             new_file_hashes[file_path] = calculate_hash(file_path)
#
#         for tracked_file in tracked_files_relative_paths:
#             file_path = metadir / tracked_file
#             if file_path not in new_file_hashes:
#                 changed.append(f"-d {file_path}")
#             elif calculate_hash(file_path) != new_file_hashes[file_path]:
#                 changed.append(f"-m {file_path}")
#                 del new_file_hashes[file_path]
#
#         for key in new_file_hashes.keys():
#             changed.append(f"-a {key}")
#
#     changed_file_path = vcs_file_path / CHANGED_FILE_NAME
#     with open(changed_file_path, "w") as changed_file:
#         changed_file.write("\n".join(changed))
