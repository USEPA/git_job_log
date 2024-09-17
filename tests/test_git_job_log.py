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
    for job in jobs:
        gjl.log_run(job)
        time.sleep(2)
    job_ran = gjl.last_runs()
    print('XXXXXX', job_ran)

    assert set(job_ran) == set(jobs)
    first = min(i.timestamp for i in job_ran.values())
    last = max(i.timestamp for i in job_ran.values())
    (last-first).total_seconds() > 6
    (last-first).total_seconds() < 7

    shutil.rmtree(gjl.local)
