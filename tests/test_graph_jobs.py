"""Tests for graph_jobs."""

import os
import random
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
    # Can return one more than requested for trailing /
    assert max(sixteen) <= 17
    assert max(twenty) <= 21
    assert max(twenty) > 17  # Make sure we get some longer ones.


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

    if os.environ.get("GIT_JOB_LOG_SHOW_TESTS"):
        graph_jobs.make_plot(graph, "test0_basic_graph.svg")


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

    if os.environ.get("GIT_JOB_LOG_SHOW_TESTS"):
        graph_jobs.make_plot(graph, "test1_all_done.svg")


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

    if os.environ.get("GIT_JOB_LOG_SHOW_TESTS"):
        graph_jobs.make_plot(graph, "test2_none_done.svg")


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

    if os.environ.get("GIT_JOB_LOG_SHOW_TESTS"):
        graph_jobs.make_plot(graph, "test3_no_get_gas.svg")


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

    if os.environ.get("GIT_JOB_LOG_SHOW_TESTS"):
        graph_jobs.make_plot(graph, "test4_updated_get_gas.svg")


def build_random_tree(
    edges: list[(int, int)],  # List of edges
    node: int,  # Current node
    idx: int,  # Next available idx for new nodes
    depth: int = 0,
):
    """Random branching tree."""
    max_depth = 4
    min_len = 5
    max_len = 10
    max_branches = 4
    branch_prob = max_branches / ((min_len + max_len) / 2)
    branches = 0
    for i in range(random.randrange(min_len, max_len + 1) + 1):
        edges.append((node, idx))
        next_node = idx
        idx += 1
        if (
            depth < max_depth
            and branches < max_branches
            and random.uniform(0, 1) < branch_prob
        ):
            branches += 1
            idx = build_random_tree(edges, node, idx, depth=depth + 1)
        node = next_node

    return idx


def test_graph_large(random_remote):
    """Test with a large graph.

    Mostly useful for visual inspection with GIT_JOB_LOG_SHOW_TESTS.
    """
    gjl = GitJobLog(random_remote)
    depends = []
    build_random_tree(depends, 1, 2)
    depends = [(str(i[0]), str(i[1])) for i in depends]
    graph = graph_jobs.make_graph(depends)
    vertices = set(chain.from_iterable(depends))
    vertices = [i for i in vertices if int(i) < 100 or random.uniform(0, 1) < 0.95]
    gjl.log_run(vertices)
    graph_jobs.add_status(graph, gjl)
    out_path = random_remote / "test.svg"
    graph_jobs.make_plot(graph, out_path, with_key=False)
    assert out_path.exists()

    if os.environ.get("GIT_JOB_LOG_SHOW_TESTS"):
        graph_jobs.make_plot(graph, "test5_large.svg")
