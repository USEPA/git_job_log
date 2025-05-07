"""Tests for git_job_log."""

import hashlib
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from git_job_log import GitJobLog
from git_job_log.git_job_log import GIT_JOB_LOG_DATA_DIR, GIT_JOB_LOG_RUN_FILE


def test_local_path(random_remote):
    """Test creation of local checkout."""
    subpath = hashlib.sha256(str(random_remote).encode("utf8")).hexdigest()
    path = Path(f"{GIT_JOB_LOG_DATA_DIR}/repos/{subpath}").expanduser().resolve()
    assert not path.exists()
    gjl = GitJobLog(random_remote, silent=False)
    assert path.exists()

    shutil.rmtree(gjl.local)


def test_log_run(random_remote):
    "Test logging a run."
    gjl = GitJobLog(random_remote)
    job = "a/job"
    job_file = gjl.local / job / GIT_JOB_LOG_RUN_FILE
    assert not job_file.exists()
    gjl.log_run([job])
    assert job_file.exists()

    shutil.rmtree(gjl.local)


@pytest.mark.parametrize("what", [None, "", "this text", {"info": 42}])
def test_last_ran(random_remote, what):
    """Test reporting of last ran time for a job."""
    gjl = GitJobLog(random_remote)
    job = "this/job/here"
    gjl.log_run([job], what)
    job_file = gjl.local / job / GIT_JOB_LOG_RUN_FILE
    last_ran = gjl.last_ran(job)
    # Jobs logged with data=None will report ""
    assert last_ran.data == (what or ""), job_file.read_text()
    assert 0 <= (datetime.now(tz=timezone.utc) - last_ran.timestamp).total_seconds() < 3

    shutil.rmtree(gjl.local)


def test_last_runs(random_remote):
    """Test reporting several jobs and timing between them."""
    gjl = GitJobLog(random_remote)
    jobs = "1/2", "2/3", "2/3/4"
    sleep = 0  # Only pause between logging, not before / after
    for job in jobs:
        time.sleep(sleep)
        sleep = 2
        gjl.log_run([job])

    job_ran = gjl.last_runs()

    assert set(job_ran) == set(jobs)
    first = min(i.timestamp for i in job_ran.values())
    last = max(i.timestamp for i in job_ran.values())
    assert (last - first).total_seconds() >= 4
    assert (last - first).total_seconds() < 6  # 5.0 seen
    assert len(job_ran) == 3

    shutil.rmtree(gjl.local)


def test_multi(random_remote):
    """Test reporting several jobs at once."""
    gjl = GitJobLog(random_remote)
    jobs = "1/2", "2/3", "2/3/4"
    gjl.log_run(jobs)

    job_ran = gjl.last_runs()

    assert set(job_ran) == set(jobs)
    first = min(i.timestamp for i in job_ran.values())
    last = max(i.timestamp for i in job_ran.values())
    assert (last - first).total_seconds() == 0
    assert len(job_ran) == 3

    shutil.rmtree(gjl.local)


def test_repeated(random_remote):
    """Test repeated reporting generates new commits."""
    gjl = GitJobLog(random_remote)
    jobs = "1/2", "2/3", "2/3/4"
    gjl.log_run(jobs)
    time.sleep(2)
    gjl.log_run(jobs[:1])  # Just the first one.

    job_ran = gjl.last_runs()

    assert set(job_ran) == set(jobs)
    first = min(i.timestamp for i in job_ran.values())
    last = max(i.timestamp for i in job_ran.values())
    assert (last - first).total_seconds() >= 2
    assert (last - first).total_seconds() < 4
    assert len(job_ran) == 3
    assert job_ran["1/2"].timestamp != job_ran["2/3"].timestamp
    assert job_ran["2/3"].timestamp == job_ran["2/3/4"].timestamp

    shutil.rmtree(gjl.local)
