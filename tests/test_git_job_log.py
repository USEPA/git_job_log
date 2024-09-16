"""Tests for git_job_log."""

import hashlib
import shutil
from pathlib import Path

import pytest

from git_job_log import GitJobLog
from git_job_log.git_job_log import GIT_JOB_LOG_RUN_FILE


def test_local_path(random_remote):
    subpath = hashlib.sha256(str(random_remote).encode("utf8")).hexdigest()
    path = Path(f"~/.git_job_log/repos/{subpath}").expanduser().resolve()
    assert not path.exists()
    gjl = GitJobLog(random_remote)
    assert path.exists()

    shutil.rmtree(gjl.local)


def test_log_run(random_remote):
    gjl = GitJobLog(random_remote)
    subpath = hashlib.sha256(str(random_remote).encode("utf8")).hexdigest()
    job = subpath
    assert not (gjl.local / subpath / GIT_JOB_LOG_RUN_FILE).exists()
    gjl.log_run(job)
    assert (gjl.local / subpath / GIT_JOB_LOG_RUN_FILE).exists()


@pytest.mark.parametrize("what", [None, "this text", {"info": 42}])
def test_last_run(random_remote, what):
    gjl = GitJobLog(random_remote)
    subpath = hashlib.sha256(str(random_remote).encode("utf8")).hexdigest()
    job = subpath
    gjl.log_run(job, what)
    assert gjl.last_ran(job).data == (what or "")

    shutil.rmtree(gjl.local)
