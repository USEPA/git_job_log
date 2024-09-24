# Git Job Log

## API / Theory of operation

Use a git repo. to log runs of "jobs".  Part of a data-pipeline DAG dependency
mapper.

Jobs have hierarchical identifiers like "home/yard/lawn/mow",
"home/yard/fence/paint", "work/commute/bus-pass/renew".

    GitJobLog.log_run(["home/yard/fence/paint"])

creates a new commit of `<repo_path>/home/yard/fence/paint/RUN` which will be a
zero byte file(*).

    GitJobLog.log_run(["home/yard/fence/paint"], data)

will write the str(ing) or bytes `data` to `RUN`, or, if `data` is not str or
bytes, the YAML representation of data.

    GitJobLog.last_ran("home/yard/fence/paint")

will return a `GitJobLog.RunLog(last_run=datetime, data=str|obj)`, add
`as_text=True` to prevent an attempt to YAML decode `data`.

    GitJobLog.last_runs()

returns a `{job_id0: RunLog, job_id1: RunLog, ...}` mapping for all jobs.

`GIT_RUN_LOG_REPO` needs to be set and can be set in .env

The expectation is that only the `main` branch is used, using other branches or
making a different branch the default on the remote may have undefined effects.

Although the `data` parameter allows storing info. about a run, currently
there's not concept of run "state" - the intent is to log only successful runs.

(*) To handle repeated logging (commits) of a job ID without changing data, the
text `### UPDATE: <date>` will be added to the end of RUN files that don't
differ.

## CLI

See the [src/git_job_log/cli.py](src/git_job_log/cli.py) doc. string for simple CLI
docs.
