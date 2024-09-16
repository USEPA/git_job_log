"""Use a git repo. to log runs of "jobs".

Jobs have hierarchical identifiers like "home/yard/lawn/mow", "home/yard/fence/paint",
"work/commute/bus-pass/renew".

    GitJobLog.log_run("home/yard/fence/paint")

creates a new commit of `<repo_path>/home/yard/fence/paint/RUN` which will be a zero
byte file.

    GitJobLog.log_run("home/yard/fence/paint", data)

will write the str(ing) or bytes `data` to `RUN`, or, if `data` is not str or bytes,
the YAML representation of data.

    GitJobLog.last_run("home/yard/fence/paint")

will return a `GitJobLog.RunLog(last_run=datetime, data=str|obj)`, add `as_text=True`
to prevent an attempt to YAML decode `data`.

    GitJobLog.all_runs()

returns a `{job_id0: RunLog, job_id1: RunLog, ...}` mapping for all jobs.

See `template.env` for git repo. settings etc.
"""

import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from dotenv import load_dotenv

GIT_JOB_LOG_DATA_DIR = ".git_job_log"
GIT_JOB_LOG_RUN_FILE = "RUN"


JobType = str


class LastRun(NamedTuple):
    """Last run information for a job."""

    timestamp: datetime | None
    data: str | dict | None


class GitJobLog:
    """Manage logging job runs to a git repo."""

    def __init__(
        self,
        remote: Path | None = None,  # repo. URL +/- token or None for auto-discovery
    ):
        """Bind to a repository."""
        if remote is None:
            remote = self._find_url()
        self.remote = remote
        self.local = self.get_or_create_local()

    @staticmethod
    def _find_url() -> Path:
        """Find .env working up the file tree and read vars."""
        paths = [Path("."), *Path(".").parents]
        for path in paths:
            if (path / ".env").exists():
                load_dotenv(path / ".env")
                repo = os.environ.get("GIT_JOB_LOG_REPO")
                if repo is not None:
                    return Path(repo)
                break

        raise Exception("Could not find .env file.")

    @staticmethod
    def _do_cmd(cmd: str | list[str | Path], silent: bool = False) -> str:
        if isinstance(cmd, str):
            cmd = cmd.split()
        if not silent:
            print(cmd)
        proc = subprocess.run(cmd, capture_output=True, check=True)  # noqa:S603
        if proc.stderr:
            print(proc.stderr.decode("utf8"))
        return proc.stdout.decode("utf8")

    def local_path(self) -> Path:
        subpath = hashlib.sha256(str(self.remote).encode("utf8")).hexdigest()
        return Path(f"~/{GIT_JOB_LOG_DATA_DIR}/repos/{subpath}").expanduser().resolve()

    def get_or_create_local(self) -> Path:
        self.local = self.local_path()
        if not self.local.exists():
            self.local.mkdir(parents=True, exist_ok=True)
            self._do_cmd(["git", "-C", self.local, "init"])
        return self.local

    def log_run(self, job: JobType, data: dict | str | None = None) -> None:
        if data is None:
            data = ""
        job = job.strip("/")
        (self.local / job).mkdir(parents=True, exist_ok=True)
        (self.local / job / GIT_JOB_LOG_RUN_FILE).write_text(data)

    def last_run(self, job: JobType) -> LastRun:
        """LastRun info. for this job."""
        if not (self.local / job).exists():
            return LastRun(timestamp=None, data=None)
