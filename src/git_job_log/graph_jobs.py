"""Plot job dependencies and status."""
import time

import pygraphviz as pgv
from git_job_log import LastRun

FILL_GOOD = "#88aaff"
FILL_BAD = "orange"


def make_graph(depends):
    """Make graph graph from edge list."""
    graph = pgv.AGraph()
    for edge in depends:
        graph.add_edge(edge)
    graph.graph_attr["label"] = time.asctime()
    graph.edge_attr["dir"] = "forward"
    # graph.node_attr["fontname"] = "sans-serif"
    return graph


def add_key(graph):
    """Add a key, use after tests are run."""
    key = graph.add_subgraph(None, "cluster_key")
    key.graph_attr["label"] = "Key"
    # key.graph_attr["ranksep"] = 0.5
    key_nodes = ("current_", "stale_")
    key.add_edge(key_nodes)
    edge = key.get_edge(*key_nodes)
    edge.attr["style"] = "invis"
    for node_id in key_nodes:
        node = key.get_node(node_id)
        node.attr["shape"] = "box"
        node.attr["width"] = 1
        node.attr["label"] = node_id.strip("_").title()
        node.attr["style"] = "filled"
        node.attr["fillcolor"] = {"current_": FILL_GOOD, "stale_": FILL_BAD}[node_id]


def label(node_id: str, max_len: int = 16) -> str:
    """Node label from node_id.

    Returns labels no more than max_len+1 long, +1 for trailing /."
    """
    texts = [[]]
    steps = node_id.split("/")
    for step_i, step in enumerate(steps):
        if texts[-1]:
            texts[-1].append("/")
        if sum(map(len, texts[-1])) + len(step) > max_len:
            texts.append([])
        texts[-1].append(step)

    return "\\n".join("".join(i) for i in texts)


def make_plot(graph, out_path, with_key=True):
    """Make SVG plot of graph."""
    for node_id in graph:
        node = graph.get_node(node_id)
        node.attr["label"] = label(node_id)
        node.attr["tooltip"] = f"{node_id}\\nlast_ran: {node.attr['run_at']}"
    if with_key:
        add_key(graph)
    graph.draw(out_path, prog="dot")


def recurse_status(graph, head, job_ran, ok):
    """Recursively set status of jobs."""
    graph.get_node(head).attr["style"] = "filled"
    graph.get_node(head).attr["run_at"] = (
        job_ran[head].timestamp if job_ran[head].timestamp else "NEVER"
    )
    if not ok:
        graph.get_node(head).attr["fillcolor"] = FILL_BAD
        for child in graph.out_neighbors(head):
            recurse_status(graph, child, job_ran, ok)
    for child in graph.out_neighbors(head):
        ok = (
            job_ran[head].timestamp is not None
            and job_ran[child].timestamp is not None
            and job_ran[child].timestamp >= job_ran[head].timestamp
        )
        recurse_status(graph, child, job_ran, ok)


def add_status(graph, gjl):
    """Add up to dateness."""
    job_ran = gjl.last_runs()
    for job in graph:
        if job not in job_ran:
            job_ran[job] = LastRun(timestamp=None, data=None)

    for node_id in graph:
        node = graph.get_node(node_id)
        node.attr["fillcolor"] = FILL_GOOD
        node.attr["style"] = "filled"
    in_degree = dict(zip(graph, graph.in_degree()))
    heads = [i for i in graph if in_degree[i] == 0]
    for head in heads:
        recurse_status(graph, head, job_ran, ok=job_ran[head].timestamp is not None)
