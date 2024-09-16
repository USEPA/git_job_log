"""Tests for git_job_log."""

import hashlib
import shutil
from pathlib import Path

from git_job_log import GitJobLog


def test_local_path(random_remote):
    subpath = hashlib.sha256(str(random_remote).encode("utf8")).hexdigest()
    path = Path(f"~/.git_job_log/repos/{subpath}").expanduser().resolve()
    assert not path.exists()
    gjl = GitJobLog(random_remote)
    assert path.exists()
    job = subpath
    assert not (gjl.local / subpath).exists()
    gjl.log_run(job)
    assert (gjl.local / subpath).exists()

    shutil.rmtree(gjl.local)
