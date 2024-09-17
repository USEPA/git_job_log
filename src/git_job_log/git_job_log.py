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
        proc = subprocess.run(cmd, capture_output=True, check=False)  # noqa:S603
        if proc.stderr:
            print(proc.stderr.decode("utf8"))
        return proc.stdout.decode("utf8")

    def pull(self) -> None:
        self._do_cmd(["git", "-C", self.local, "pull"])

    def local_path(self) -> Path:
        subpath = hashlib.sha256(str(self.remote).encode("utf8")).hexdigest()
        return Path(f"~/{GIT_JOB_LOG_DATA_DIR}/repos/{subpath}").expanduser().resolve()

    def get_or_create_local(self) -> Path:
        self.local = self.local_path()
        if not self.local.exists():
            self.local.mkdir(parents=True, exist_ok=True)
            self._do_cmd(["git", "clone", self.remote, self.local])
            self._do_cmd(["git", "-C", self.local, "checkout", "-b", "main"])
            self._do_cmd(["git", "-C", self.local, "checkout", "main"])
        return self.local

    def log_run(self, job: JobType, data: dict | str | None = None) -> None:
        self.pull()
        if data is None:
            data = ""
        if not isinstance(data, str):
            try:
                data = yaml.safe_dump(data)
            except yaml.representer.RepresenterError:
                data = str(data)
        job = job.strip("/")
        (self.local / job).mkdir(parents=True, exist_ok=True)
        job_file = self.local / job / GIT_JOB_LOG_RUN_FILE
        job_file.write_text(data)
        self._do_cmd(["git", "-C", self.local, "add", "-A"])
        self._do_cmd(["git", "-C", self.local, "commit", "-m", f"{job} run"])
        self._do_cmd(
            ["git", "-C", self.local, "push", "--set-upstream", "origin", "main"]
        )

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
        git ls-tree -r --name-only HEAD | \
            xargs -IF git --no-pager log -1 --format='%cI F' F
        """
        self.pull()
        file_list = self._do_cmd(
            ["git", "-C", self.local, "ls-tree", "-r", "--name-only", "HEAD"]
        ).split("\n")
        file_list = [i.rsplit("/", 1)[0] for i in file_list if i.strip()]
        return {job: self.last_ran(job, batch=True) for job in file_list}
