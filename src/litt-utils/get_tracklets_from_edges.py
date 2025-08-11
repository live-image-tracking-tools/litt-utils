from __future__ import annotations

import os
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np
import zarr

from .metadata_schema import GeffMetadata

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


def validate(path: str | Path):
@@ -89,3 +92,100 @@ def validate(path: str | Path):
                        f"Edge property {prop} missing mask has length {missing_len}, "
                        f"which does not match id length {edge_id_len}"
                    )


def get_tracklets_from_edges(
    edge_list: np.ndarray,
) -> tuple[dict[Any, int], dict[int, list[int]]]:
    """Extract tracklet IDs and parent-child tracklet connections from an edge list.
    Parameters
    ----------
    edge_list : np.ndarray
        An (N, 2) numpy array where each row `[u, v]` represents a directed
        edge from node `u` to node `v`.
    Returns
    -------
    Tuple[Dict[Any, int], Dict[int, List[int]]]
        A tuple containing:
        - A dictionary mapping each node ID to its assigned tracklet ID.
        - A dictionary mapping each child tracklet ID to a list of its parent
          tracklet IDs, representing the graph of tracklets.
    """
    if not isinstance(edge_list, np.ndarray) or edge_list.ndim != 2 or edge_list.shape[1] != 2:
        raise ValueError("edge_list must be an (N, 2) numpy array.")

    # build adjacency lists and find all unique nodes from the edge list
    successors = defaultdict(list)
    predecessors = defaultdict(list)
    nodes = np.unique(edge_list)

    for u, v in edge_list:
        successors[u].append(v)
        predecessors[v].append(u)

    # Initialise variables for tracklet identification
    track_id = 1
    visited_nodes = set()
    node_to_tid = {}
    parent_graph = defaultdict(list)  # Maps a child node to a list of its parent nodes

    # Iterate through all nodes to ensure every component is visited
    for node in nodes:
        if node in visited_nodes:
            continue

        # Trace back to find the beginning of the tracklet
        start_node = node
        while len(predecessors.get(start_node, [])) == 1:
            predecessor = predecessors[start_node][0]
            if predecessor in visited_nodes:
                break
            start_node = predecessor

        # Go forward along the path to build the current tracklet
        current_tracklet = []
        temp_node = start_node
        while True:
            current_tracklet.append(temp_node)
            visited_nodes.add(temp_node)

            # A tracklet ends if the node is a split point (>1 successor) or a leaf (0 successors)
            if len(successors.get(temp_node, [])) != 1:
                # This node should be a parent to all its successors' tracklets
                for child in successors.get(temp_node, []):
                    parent_graph[child].append(temp_node)
                break

            successor = successors[temp_node][0]

            # A tracklet also ends if its successor is a merge point (>1 predecessor)
            if len(predecessors.get(successor, [])) != 1:
                parent_graph[successor].append(temp_node)
                break

            temp_node = successor

        # Assign the same track_id to all nodes in this discovered tracklet
        for node_id in current_tracklet:
            node_to_tid[node_id] = track_id
        track_id += 1

    # Build the final tracklet graph from the parent-child node relationships
    track_graph = defaultdict(list)
    for child_node, parent_nodes in parent_graph.items():
        # Ensure the child and parent nodes were actually assigned to a tracklet
        if child_node not in node_to_tid:
            continue

        child_tid = node_to_tid[child_node]
        for parent_node in parent_nodes:
            if parent_node in node_to_tid:
                parent_tid = node_to_tid[parent_node]
                track_graph[child_tid].append(parent_tid)

    # Convert to a regular dictionary with unique, sorted parent IDs
    final_tracklet_graph = {child: sorted(set(parents)) for child, parents in track_graph.items()}

    return node_to_tid, final_tracklet_graph
