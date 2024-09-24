"""Tests for graph_jobs."""

from itertools import chain

from git_job_log import GitJobLog, LastRun, graph_jobs

DEPENDS = [
    ("home/yard/season/spring", "home/yard/lawn/get_gas"),
    ("home/yard/lawn/get_gas", "home/yard/lawn/mow"),
    ("home/yard/lawn/mow", "home/yard/lawn/compost_clippings"),
    ("home/yard/lawn/get_gas", "home/yard/tools/find/gas_tank"),
    ("home/yard/tools/find/gas_tank", "home/yard/shed/organize"),
]

VERTICES = list(set(chain.from_iterable(DEPENDS)))


def test_make_graph():
    graph = graph_jobs.make_graph(DEPENDS)
    assert min(graph.degree(mode="in")) == 0
    assert max(graph.degree(mode="in")) == 1
    assert min(graph.degree(mode="out")) == 0
    assert max(graph.degree(mode="out")) == 2
    assert len(graph.vs) == len(VERTICES)


def test_graph_jobs(random_remote):
    """Test we can just graph the jobs"""
    gjl = GitJobLog(random_remote)
    job_ran = gjl.last_runs()
    for job in VERTICES:
        if job not in job_ran:
            job_ran[job] = LastRun(timestamp=None, data=None)
    graph = graph_jobs.make_graph(DEPENDS)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path)
    graph_jobs.make_plot(graph, "test2.svg")
    graph.write_svg("test3.svg", layout=layout)
    assert out_path.exists()
    text = out_path.read_text()
    print(VERTICES)
    assert all([i in text for i in VERTICES])
