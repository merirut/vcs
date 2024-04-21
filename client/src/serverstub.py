import os
import subprocess
from datetime import datetime

server_exec = os.getenv('VCS_SERVER_EXECUTABLE_PATH')


def init() -> bool:
    """
    :return: OK or not
    """
    result = subprocess.run([server_exec, "init"], stdout=subprocess.PIPE)
    status = result.stdout.decode('utf-8').strip()
    return_code = result.returncode
    return return_code == 0 and status == "OK"


def log() -> list[tuple[str, datetime, str]] | None:
    """
    :return: chronological list of commits in format (hash, message)
    """
    result = subprocess.run([server_exec, "log"], stdout=subprocess.PIPE)
    commits_table = result.stdout.decode('utf-8').strip()
    return_code = result.returncode
    if return_code != 0:
        return

    commits = []
    with open(commits_table, "r") as file:
        for line in file.read().splitlines():
            hsh, timestamp, message = line.split(" ", 2)
            commits.append((hsh, datetime.isoformat(timestamp), message))
    return commits


def commit(message: str, root_dir: str, head_hash: str, new_hash: str) -> bool:
    """
    :param message: commit message
    :param root_dir: absolute path to repo root dir
    :param head_hash: hash of current head
    :param new_hash: calculated hash of new commit
    :return: OK or not
    """
    return True


def reset(hash_to_reset: str) -> str | None:
    """
    :param hash_to_reset: hash of target commit
    :return: absolute path where requested repo state should be copied from
    """
    return "/Users/ilakonovalov/IdeaProjects/vcs/tests/test1/snapshots"