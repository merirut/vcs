import hashlib


def calculate_hash_for_file(file_path):
    sha = hashlib.sha256()
    file_path = str(file_path)
    sha.update(file_path.encode('utf-8'))

    with open(file_path, 'rb') as f:
        sha.update(f.read())
    return sha.hexdigest()


def calculate_hash_for_files(tracked_files: dict[str, str]) -> tuple[str, dict[str, str]]:
    sha_by_path = {}
    global_sha = hashlib.sha256()
    sorted_files = sorted(map(lambda x: str(x), tracked_files.keys()))
    for file in sorted_files:
        local_sha = hashlib.sha256()
        local_sha.update(file.encode('utf-8'))
        with open(file, 'rb') as f:
            local_sha.update(f.read())
        local_sha = local_sha.hexdigest()
        sha_by_path[file] = local_sha
        global_sha.update(local_sha.encode('utf-8'))
    return global_sha.hexdigest(), sha_by_path
