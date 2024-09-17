"""Use a git repo. to log runs of "jobs".

Jobs have hierarchical identifiers like "home/yard/lawn/mow", "home/yard/fence/paint",
"work/commute/bus-pass/renew".

    GitJobLog.log_run(["home/yard/fence/paint"])

creates a new commit of `<repo_path>/home/yard/fence/paint/RUN` which will be a zero
byte file.

    GitJobLog.log_run(["home/yard/fence/paint"], data)

will write the str(ing) or bytes `data` to `RUN`, or, if `data` is not str or bytes,
the YAML representation of data.

    GitJobLog.last_ran("home/yard/fence/paint")

will return a `GitJobLog.RunLog(last_run=datetime, data=str|obj)`, add `as_text=True`
to prevent an attempt to YAML decode `data`.

    GitJobLog.last_runs()

returns a `{job_id0: RunLog, job_id1: RunLog, ...}` mapping for all jobs.

GIT_RUN_LOG_REPO needs to be set and can be set in .env
"""

import hashlib
import os
import subprocess
import time
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import NamedTuple

import yaml
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
        silent: bool = True,  # Don't report noisy git msg.s
    ):
        """Bind to a repository."""
        self.silent = silent
        if not self.silent:
            print("IMPORTANT: git warnings below are typically OK / expected.")
        if remote is None:
            remote = self._find_url()
        self.remote = remote
        self.local = self.get_or_create_local()

    @staticmethod
    def _find_url() -> str:
        """Find .env working up the file tree and read vars."""
        repo = os.environ.get("GIT_JOB_LOG_REPO")
        if repo and repo.strip():
            return repo
        paths = [Path("."), *Path(".").parents]
        for path in paths:
            if (path / ".env").exists():
                load_dotenv(path / ".env")
                repo = os.environ.get("GIT_JOB_LOG_REPO")
                if repo is not None:
                    return repo
                break

        raise Exception("Could not find .env file for GIT_JOB_LOG_REPO")

    def _do_cmd(self, cmd: str | list[str | Path]) -> str:
        """Run a command, show feedback if not supressed."""
        if isinstance(cmd, str):
            cmd = cmd.split()
        if not self.silent:
            print(cmd)
        proc = subprocess.run(cmd, capture_output=True, check=False)  # noqa:S603
        if proc.stderr and not self.silent:
            print(proc.stderr.decode("utf8"))
        return proc.stdout.decode("utf8")

    def pull(self) -> None:
        """Pull latest data."""
        self._do_cmd(["git", "-C", self.local, "pull"])
        self._do_cmd(["git", "-C", self.local, "reset", "--hard", "origin/main"])

    def local_path(self) -> Path:
        """Path to local checkout of remote."""
        subpath = hashlib.sha256(str(self.remote).encode("utf8")).hexdigest()
        return Path(f"~/{GIT_JOB_LOG_DATA_DIR}/repos/{subpath}").expanduser().resolve()

    def get_or_create_local(self) -> Path:
        """Create local checkout of remote if needed."""
        self.local = self.local_path()
        if not self.local.exists():
            self.local.mkdir(parents=True, exist_ok=True)
            self._do_cmd(["git", "clone", self.remote, self.local])
            self._do_cmd(["git", "-C", self.local, "checkout", "-b", "main"])
            self._do_cmd(["git", "-C", self.local, "checkout", "main"])
        return self.local

    def log_run(self, jobs: list[JobType], data: dict | str | None = None) -> None:
        """Log running of listed jobs."""
        self.pull()
        updated = datetime.now()
        if data is None:
            data = ""
        if not isinstance(data, (bytes, str)):
            try:
                data = yaml.safe_dump(data)
            except yaml.representer.RepresenterError:
                data = str(data)
        old_last_runs = self.last_runs()
        for job in jobs:
            job = job.strip("/")
            (self.local / job).mkdir(parents=True, exist_ok=True)
            job_file = self.local / job / GIT_JOB_LOG_RUN_FILE
            use_data = data
            if job_file.exists() and job_file.read_text() == data:
                # Append this to make the file different, git supports empty commits but
                # not associating unchanged files with them.
                use_data += f"### UPDATED: {updated}"
            job_file.write_text(use_data)
        self._do_cmd(["git", "-C", self.local, "add", "-A"])
        job_list = ", ".join(jobs)
        self._do_cmd(["git", "-C", self.local, "commit", "-m", f"ran: {job_list}"])
        self._do_cmd(
            ["git", "-C", self.local, "push", "--set-upstream", "origin", "main"]
        )
        last_runs = self.last_runs()
        # Check new commits are in repo. - this is the core function so need to fail if not
        errors = []
        for job in jobs:
            if job not in last_runs:
                errors.append(f"MISSING: {job}")
            else:
                if (
                    job in old_last_runs
                    and last_runs[job].timestamp == old_last_runs[job].timestamp
                ):
                    errors.append(f"NO_UPDATE: {job}")
        if errors:
            raise Exception("LOGGING JOB(S) FAILED:\n" + "\n".join(errors))

    def last_ran(self, job: JobType, batch=False) -> LastRun:
        """LastRun info. for this job."""
        if not batch:
            self.pull()
        job_file = self.local / job / GIT_JOB_LOG_RUN_FILE
        if not job_file.exists():
            return LastRun(timestamp=None, data=None)
        last = self._do_cmd(
            [
                "git",
                "-C",
                self.local,
                "--no-pager",
                "log",
                "-1",
                "--format=%cI",
                job_file,
            ]
        ).strip()

        data = job_file.read_text()
        try:
            if data.strip():  # Don't change ""
                data = yaml.safe_load(data)
        except yaml.scanner.ScannerError:
            pass

        return LastRun(timestamp=datetime.fromisoformat(last), data=data)

    def last_runs(self) -> dict:
        """
        List last run time for all jobs.

        git ls-tree -r --name-only HEAD | \
            xargs -IF git --no-pager log -1 --format='%cI F' F
        """
        self.pull()
        file_list = self._do_cmd(
            ["git", "-C", self.local, "ls-tree", "-r", "--name-only", "HEAD"]
        ).split("\n")
        file_list = [i.rsplit("/", 1)[0] for i in file_list if i.strip()]
        return {job: self.last_ran(job, batch=True) for job in file_list}