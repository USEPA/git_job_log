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

The expectation is that only the `job_logs` branch is used, using other branches or
making a different branch the default on the remote may have undefined effects.
Git Job Log uses `reset --hard` to sync. with the remote repo., so using the default
`main` branch is slightly less safe than the dedicated `job_logs` branch.

Although the `data` parameter allows storing info. about a run, currently
there's not concept of run "state" - the intent is to log only successful runs.

Set `GIT_JOB_LOG_DEBUG` to see git commands being run.

(*) To handle repeated logging (commits) of a job ID without changing data, the
text `### UPDATE: <datetime>` will be added to the end of RUN files that don't
differ.  It is not enough to use `--allow-empty` as that doesn't identify the
"files" (jobs) that have been run.  For blank log messages this means that
every second log message will contain `### UPDATE: <datetime>`, intervening
messages "differ" simply by being blank.

## CLI

See the [src/git_job_log/cli.py](src/git_job_log/cli.py) doc. string for simple CLI
docs.

## Dev. notes

    GIT_JOB_LOG_SHOW_TESTS=1 uv run pytest -vv
    
will run tests and leave `test*.svg` files in current directory for inspection,
omit `GIT_JOB_LOG_SHOW_TESTS` for no post test files.

## Disclaimer

The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. EPA has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA. The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government. 

