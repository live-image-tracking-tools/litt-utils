from typing import Any
import networkx as nx


def get_sorted_track_ids(
    graph: nx.DiGraph,
    tracklet_id_key: str="tracklet_id"
) -> list[Any]:
    """
    Extract the lineage tree plot order of the tracklet_ids on the graph, ensuring that
    each tracklet_id is placed in between its daughter tracklet_ids and adjacent to its
    parent track id.

    Args:
        graph (nx.DiGraph): graph with a tracklet_id attribute on it.
        tracklet_id_key (str): tracklet_id key on the graph.

    Returns:
        list[Any] of ordered tracklet_ids.
    """

    # Create tracklet_id to parent_tracklet_id mapping (0 if tracklet has no parent)
    tracklet_to_parent_tracklet = {}
    for node, data in graph.nodes(data=True):
        tracklet = data[tracklet_id_key]
        if tracklet in tracklet_to_parent_tracklet:
            continue
        predecessor = next(graph.predecessors(node), None)
        if predecessor is not None:
            parent_tracklet_id = graph.nodes[predecessor][tracklet_id_key]
        else:
            parent_tracklet_id = 0
        tracklet_to_parent_tracklet[tracklet] = parent_tracklet_id

    # Final sorted order of roots
    roots = sorted([tid for tid, ptid in tracklet_to_parent_tracklet.items() if ptid == 0])
    x_axis_order = list(roots)

    # Find the children of each of the starting points, and work down the tree.
    while len(roots) > 0:
        children_list = []
        for tracklet_id in roots:
            children = [tid for tid, ptid in tracklet_to_parent_tracklet.items() 
                        if ptid == tracklet_id]
            for i, child in enumerate(children):
                [children_list.append(child)]
                x_axis_order.insert(x_axis_order.index(tracklet_id) + i, child)
        roots = children_list

    return x_axis_order