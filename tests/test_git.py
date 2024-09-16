"""Tests for git connectivity."""
import os
import time
from pathlib import Path

from git_job_log import GitJobLog


def test_add_commit(repo_url: Path) -> None:
    """Test we can connect and commit something - explicit URL."""
    gjl = GitJobLog(repo_url)
    _do_tests(gjl, repo_url)


def test_add_commit_auto(repo_url: Path) -> None:
    """Test we can connect and commit something - auto-discover URL."""
    pwd = os.getcwd()
    os.chdir(repo_url)
    (repo_url / ".env").write_text(f"GIT_JOB_LOG_REPO = {repo_url}/repo")
    gjl = GitJobLog()
    _do_tests(gjl, gjl.repo)
    os.chdir(pwd)


def _do_tests(gjl: GitJobLog, repo: Path) -> None:
    assert list(repo.glob("**/*")) == [], repo
    gjl._do_cmd(f"git init {repo}")
    text = str(time.time())
    (repo / "del.me").write_text(text)
    gjl._do_cmd(f"git -C {repo} add del.me")
    gjl._do_cmd(["git", "-C", repo, "commit", "-am", "changed time"])
    assert (repo / "del.me").read_text() == text
