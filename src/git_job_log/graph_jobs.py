"""Plot job dependencies and status."""
from itertools import chain

import igraph


def make_graph(depends):
    """Make igraph graph from edge list."""
    graph = igraph.Graph(directed=True)
    graph.add_vertices(list(set(chain.from_iterable(depends))))
    graph.add_edges(depends)
    return graph


def make_plot(graph, out_path):
    """Make SVG plot of graph."""
    layout = graph.layout("tree")
    graph.vs["label"] = graph.vs["name"]
    igraph.plot(graph, out_path, layout=layout, margin=150, bbox=(600,) * 2)
