"""Command line for git_job_log.

usage: cli.py [-h] [--verbose] [COMMAND] [JOB(S) ...]

positional arguments:
  COMMAND     Mode: list, log (default: list)
  JOB(S)      Job IDs: e.g. 'work/commute/pass/renew' (default: None)

options:
  -h, --help  show this help message and exit
  --verbose   Show git commands and responses. (default: False)
"""

import argparse
import sys

from git_job_log import GitJobLog


def _build_GitJobLog(opt):
    """Tweak silent flag etc."""
    gjl = GitJobLog()
    if opt.verbose:
        gjl.silent = False
    return gjl


def make_parser() -> argparse.ArgumentParser:
    """Make command line parser."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "command",
        type=str,
        default="list",
        nargs="?",
        metavar="COMMAND",
        help="Mode: list, log",
    )
    parser.add_argument(
        "job",
        type=str,
        nargs="*",
        metavar="JOB(S)",
        help="Job IDs: e.g. 'work/commute/pass/renew'",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Show git commands and responses.",
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        default=False,
        help="Allow user to edit commit log.",
    )
    return parser


def list_last_runs(opt):
    """List the last runs of all jobs."""
    gjl = _build_GitJobLog(opt)
    for job, run in gjl.last_runs().items():
        print(run.timestamp, job)


def log_run(opt):
    """Log a successful run of the job(s) listed on the commandline."""
    gjl = _build_GitJobLog(opt)
    gjl.log_run(opt.job, edit=opt.edit)


DISPATCH = {
    "list": list_last_runs,
    "log": log_run,
}

if __name__ == "__main__":
    opt = make_parser().parse_args(sys.argv[1:])
    DISPATCH[opt.command](opt)
