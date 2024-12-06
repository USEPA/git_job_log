"""Plot job dependencies and status."""
import time
from collections import defaultdict

import pygraphviz as pgv

from git_job_log import LastRun
from git_job_log.util import job_match

FILL_GOOD = "#88aaff"
FILL_BAD = "orange"


# list of distinct colors from https://sashamaps.net/docs/resources/20-colors/
# the distinctness and appeal decreases as you go down the list, so zip()ing with
# a fixed order list of fp_ids is probably fine.
COLORS = [
    "#e6194B",  # Red
    "#3cb44b",  # Green
    "#ffe119",  # Yellow
    "#4363d8",  # Blue
    "#f58231",  # Orange
    "#911eb4",  # Purple
    "#42d4f4",  # Cyan
    "#f032e6",  # Magenta
    "#bfef45",  # Lime
    "#fabed4",  # Pink
    "#469990",  # Teal
    "#dcbeff",  # Lavender
    "#9A6324",  # Brown
    # "#fffac8",  # Beige
    "#800000",  # Maroon
    "#aaffc3",  # Mint
    "#808000",  # Olive
    # "#ffd8b1",  # Apricot
    "#000075",  # Navy
    "#a9a9a9",  # Grey
]


def make_graph(depends):
    """Make graph graph from edge list."""
    graph = pgv.AGraph(directed=True)
    for edge_i, edge in enumerate(depends):
        # Tried making the edge colors more stable by hashing the edge, but
        # this is better for not re-using the same colors in the same area of
        # the graph.
        graph.add_edge(edge, color=COLORS[edge_i % len(COLORS)], penwidth=3)
    graph.graph_attr["label"] = time.asctime()
    graph.graph_attr["rankdir"] = "LR"
    graph.graph_attr["concentrate"] = "true"  # Not working?  Even without color.
    graph.node_attr["fontname"] = "sans-serif"
    graph._label = defaultdict(list)
    graph._description = defaultdict(list)
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


def annotate_graph(graph, description: dict | None = None) -> None:
    """Add labels and tooltips to graph."""
    if description is None:
        description = {}
    for node_id in graph:
        graph._label[node_id] = [node_id]
        graph._description[node_id] = [
            description[k] for k in description if job_match(node_id, k)
        ]


def make_plot(graph, out_path, with_key=True) -> None:
    """Make a plot of graph.

    Format depends on out_path extension.
    """
    for node_id in graph:
        node = graph.get_node(node_id)
        labels = graph._label[node_id]
        if not labels:
            continue  # A node in the key
        node.attr["label"] = label(labels[0])
        if len(labels) > 1:
            node.attr["label"] += f"\\n+{len(labels) - 1}"
        description = ["\\n".join(sorted(labels))]
        notes = "\\n".join(sorted(set(graph._description[node_id])))
        if notes:
            description.append(notes)
        description.append("Last run: " + (node.attr.get("run_at") or "NEVER"))
        node.attr["tooltip"] = "\\n".join(description)
    if with_key:
        add_key(graph)
    graph.draw(out_path, prog="dot")


def squash_graph(graph):
    """Collapse nodes that are only alternate paths between two other nodes."""
    for node in graph.iternodes():
        child_destinations = {
            k: set(graph.successors(k)) for k in graph.successors(node)
        }
        # Children with only one destination.
        child_destinations = {
            k: v for k, v in child_destinations.items() if len(v) == 1
        }
        out_paths = defaultdict(set)
        for child, destinations in child_destinations.items():
            out_paths[next(iter(destinations))].add(child)
        # Destinations reached by multiple single-destination children.
        out_paths = {k: v for k, v in out_paths.items() if len(v) > 1}
        for parallel_paths in out_paths.values():
            paths = list(parallel_paths)
            keep = paths.pop(0)
            for child in paths:
                merge_nodes(graph, keep, child)
                graph.remove_node(child)


def merge_nodes(graph, keep_id, child_id):
    """Merge child into keep."""
    graph._label[keep_id].extend(graph._label[child_id])
    graph._description[keep_id].extend(graph._description[child_id])


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
