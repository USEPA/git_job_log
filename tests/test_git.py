"""Tests for git connectivity."""
import os
import shutil
import time
from pathlib import Path

from git_job_log import GitJobLog


def test_add_commit(random_remote: Path) -> None:
    """Test we can connect and commit something - explicit URL."""
    gjl = GitJobLog(random_remote)
    _do_tests(gjl)


def test_add_commit_auto(random_remote: Path) -> None:
    """Test we can connect and commit something - auto-discover URL."""
    pwd = os.getcwd()
    os.chdir(random_remote)
    try:
        (random_remote / ".env").write_text(f"GIT_JOB_LOG_REPO = {random_remote}/repo")
        gjl = GitJobLog()
        _do_tests(gjl)
    finally:
        os.chdir(pwd)


def _do_tests(gjl: GitJobLog) -> None:
    text = str(time.time())
    (gjl.local / "del.me").write_text(text)
    gjl._do_cmd(f"git -C {gjl.local} add del.me")
    gjl._do_cmd(["git", "-C", gjl.local, "commit", "-am", "changed time"])
    assert (gjl.local / "del.me").read_text() == text
    shutil.rmtree(gjl.local)
