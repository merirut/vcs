def init() -> bool:
    """
    :return: OK or not
    """
    pass


def log() -> list[tuple[str, str]]:
    """
    :return: chronological list of commits in format (hash, message)
    """
    pass


def commit(message: str, root_dir: str, head_hash: str, new_hash: str) -> bool:
    """
    :param message: commit message
    :param root_dir: absolute path to repo root dir
    :param head_hash: hash of current head
    :param new_hash: calculated hash of new commit
    :return: OK or not
    """
    pass


def reset(hash_to_reset: str) -> str:
    """
    :param hash_to_reset: hash of target commit
    :return: absolute path where requested repo state should be copied from
    """
    pass
