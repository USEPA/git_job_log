"""Plot job dependencies and status."""

import networkx as nx
import pygraphviz as pgv


def make_graph(depends):
    """Make igraph graph from edge list."""
    graph = nx.DiGraph(directed=True)
    graph.add_edges_from(depends)
    return graph


def make_plot(graph, out_path):
    """Make SVG plot of graph."""
    dag = pgv.AGraph()
    for edge in graph.edges:
        dag.add_edge(edge)
    dag.draw(out_path, prog="dot")
