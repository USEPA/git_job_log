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

import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv


class GitJobLog:
    """Manage logging job runs to a git repo."""

    def __init__(
        self,
        repo: Path | None = None,  # repo. URL +/- token or None for auto-discovery
    ):
        """Bind to a repository."""
        if repo is None:
            repo = self._find_url()
        self.repo = repo

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
