"""Tests for git_job_log."""

import hashlib
import shutil
import time
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
    job_file = gjl.local / subpath / GIT_JOB_LOG_RUN_FILE
    assert not job_file.exists()
    gjl.log_run(job)
    assert job_file.exists()

    shutil.rmtree(gjl.local)


@pytest.mark.parametrize("what", [None, "", "this text", {"info": 42}])
def test_last_ran(random_remote, what):
    gjl = GitJobLog(random_remote)
    subpath = hashlib.sha256(str(random_remote).encode("utf8")).hexdigest()
    job = subpath
    gjl.log_run(job, what)
    job_file = gjl.local / subpath / GIT_JOB_LOG_RUN_FILE
    assert gjl.last_ran(job).data == (what or ""), job_file.read_text()

    shutil.rmtree(gjl.local)

def test_last_runs(random_remote):
    gjl = GitJobLog(random_remote)
    jobs = "1/2", "2/3", "2/3/4"
    sleep = 0
    for job in jobs:
        time.sleep(sleep)
        sleep = 2
        gjl.log_run(job)
    job_ran = gjl.last_runs()

    assert set(job_ran) == set(jobs)
    first = min(i.timestamp for i in job_ran.values())
    last = max(i.timestamp for i in job_ran.values())
    assert (last-first).total_seconds() >= 4
    assert (last-first).total_seconds() < 5

    shutil.rmtree(gjl.local)