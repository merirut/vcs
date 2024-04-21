from datetime import datetime
import socket

server_exec = 'VCS_SERVER_EXECUTABLE_PATH'
SERVER_ADDRESS = ('localhost', 8080)

def send_request(request) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(SERVER_ADDRESS)
        s.sendall(request)
        response = s.recv(4096).decode('utf-8')
        return response

def init() -> bool:
    """
    :return: OK or not
    """
    result = send_request("init".encode())
    return result == "OK"


def log() -> list[tuple[str, datetime, str]] | None:
    """
    :return: chronological list of commits in format (hash, message)
    """
    commits_table = send_request("log".encode())

    commits = []
    with open(commits_table, "r") as file:
        for line in file.read().splitlines():
            hsh, timestamp, message = line.split(" ", 2)
            commits.append((hsh, datetime.fromisoformat(timestamp), message))
    return commits


def commit(message: str, root_dir: str, head_hash: str, new_hash: str) -> bool:
    """
    :param message: commit message
    :param root_dir: absolute path to repo root dir
    :param head_hash: hash of current head
    :param new_hash: calculated hash of new commit
    :return: OK or not
    """
    request = f'commit "{message}" {root_dir} {head_hash} {new_hash}'
    result = send_request(request.encode())
    return result == "OK"


def reset(hash_to_reset: str) -> str | None:
    """
    :param hash_to_reset: hash of target commit
    :return: absolute path where requested repo state should be copied from
    """
    request = f'reset {hash_to_reset}'
    commit_dir = send_request(request.encode())
    if (commit_dir != "Error: commit not found" and commit_dir != ""):
        return commit_dir
    return None
