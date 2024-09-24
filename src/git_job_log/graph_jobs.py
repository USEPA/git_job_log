"""Plot job dependencies and status."""

import pygraphviz as pgv


def make_graph(depends):
    """Make graph graph from edge list."""
    graph = pgv.AGraph()
    for edge in depends:
        graph.add_edge(edge)
    return graph


def label(node_id: str, max_len: int = 16) -> str:
    """Node label from node_id."""
    texts = [[]]
    steps = node_id.split("/")
    for step_i, step in enumerate(steps):
        if texts[-1]:
            texts[-1].append("/")
        if sum(map(len, texts[-1])) + len(step) > max_len:
            texts.append([])
        texts[-1].append(step)

    return "\\n".join("".join(i) for i in texts)


def make_plot(graph, out_path):
    """Make SVG plot of graph."""
    for node_id in graph:
        node = graph.get_node(node_id)
        node.attr["label"] = label(node_id)
    graph.draw(out_path, prog="dot")
