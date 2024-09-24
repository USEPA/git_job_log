"""Tests for graph_jobs."""

import time
from itertools import chain

from git_job_log import GitJobLog, graph_jobs
from git_job_log.graph_jobs import FILL_BAD, FILL_GOOD

DEPENDS = [
    ("home/yard/season/spring", "home/yard/lawn/get_gas"),
    ("home/yard/lawn/get_gas", "home/yard/lawn/mow"),
    ("home/yard/lawn/mow", "home/yard/lawn/compost_clippings"),
    ("home/yard/lawn/get_gas", "home/yard/tools/find/gas_tank"),
    ("home/yard/tools/find/gas_tank", "home/yard/shed/organize"),
    # Separate tree
    ("work/commute/pass/expired", "work/commute/pass/renew"),
]

VERTICES = list(set(chain.from_iterable(DEPENDS)))


def test_make_graph():
    graph = graph_jobs.make_graph(DEPENDS)
    assert min(graph.in_degree()) == 0
    assert max(graph.in_degree()) == 1
    assert min(graph.out_degree()) == 0
    assert max(graph.out_degree()) == 2
    assert len(graph) == len(VERTICES)


def test_labels():
    """Test label lengths."""
    sixteen = [
        len(i)
        for i in chain.from_iterable(
            graph_jobs.label(j, 16).split("\\n") for j in VERTICES
        )
    ]
    twenty = [
        len(i)
        for i in chain.from_iterable(
            graph_jobs.label(j, 20).split("\\n") for j in VERTICES
        )
    ]
    assert max(sixteen) <= 17
    assert max(twenty) <= 21
    assert max(twenty) > 17


def test_graph_jobs(random_remote):
    """Test we can just graph the jobs"""
    graph = graph_jobs.make_graph(DEPENDS)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path, with_key=False)
    assert out_path.exists()
    text = out_path.read_text()
    print(VERTICES)
    # Note the full text (node_id) occurs in the <title/> element, not the label.
    assert all([i in text for i in VERTICES])

    graph_jobs.make_plot(graph, "test2.svg")


def test_graph_deps_all_done(random_remote):
    """Test with all jobs run at same time."""
    gjl = GitJobLog(random_remote)
    gjl.log_run(VERTICES)
    graph = graph_jobs.make_graph(DEPENDS)
    graph_jobs.add_status(graph, gjl)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path, with_key=False)
    assert out_path.exists()
    text = out_path.read_text()
    assert text.count("NEVER") == 0
    assert text.count(FILL_BAD) == 0
    assert text.count(FILL_GOOD) == len(VERTICES)

    graph_jobs.make_plot(graph, "test3.svg")


def test_graph_deps_none_done(random_remote):
    """Test with all jobs run at same time."""
    gjl = GitJobLog(random_remote)
    graph = graph_jobs.make_graph(DEPENDS)
    graph_jobs.add_status(graph, gjl)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path, with_key=False)
    assert out_path.exists()
    text = out_path.read_text()
    assert text.count("NEVER") == len(VERTICES)
    assert text.count(FILL_BAD) == len(VERTICES)
    assert text.count(FILL_GOOD) == 0

    graph_jobs.make_plot(graph, "test4.svg")


def test_graph_deps_some_done(random_remote):
    """Test with a job never run."""
    gjl = GitJobLog(random_remote)
    gjl.log_run(i for i in VERTICES if i != "home/yard/lawn/get_gas")
    graph = graph_jobs.make_graph(DEPENDS)
    graph_jobs.add_status(graph, gjl)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path, with_key=False)
    assert out_path.exists()
    text = out_path.read_text()
    assert text.count("NEVER") == 1  # "home/yard/lawn/get_gas"
    assert text.count(FILL_BAD) == 5  # above plus its four descendants
    assert text.count(FILL_GOOD) == len(VERTICES) - 5

    graph_jobs.make_plot(graph, "test5.svg")


def test_graph_deps_updated(random_remote):
    """Test with a job run later."""
    gjl = GitJobLog(random_remote)
    gjl.log_run(VERTICES)
    time.sleep(2)
    gjl.log_run(["home/yard/lawn/get_gas"])
    graph = graph_jobs.make_graph(DEPENDS)
    graph_jobs.add_status(graph, gjl)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path, with_key=False)
    assert out_path.exists()
    text = out_path.read_text()
    assert text.count("NEVER") == 0
    assert text.count(FILL_BAD) == 4  # "home/yard/lawn/get_gas"'s four descendants
    assert text.count(FILL_GOOD) == len(VERTICES) - 4

    graph_jobs.make_plot(graph, "test6.svg")
