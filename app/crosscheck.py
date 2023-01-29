import logging
import networkx as nx

from app.retrieve import DataRetriever


# TODO: think about overall limits on the amount of papers to be processed and returned


class EmptyGroupError(Exception):
    pass


def build_graph(groups):
    graph = nx.DiGraph()
    node_groups = []

    for group_papers in groups:
        nodes = []
        for paper_link in group_papers:
            paper = DataRetriever.get_paper_data(paper_link, fields=['paperId'])
            if not paper:
                logging.info(f'Paper {paper_link} was not found, continue')
                continue
            paper_id = paper['paperId']

            # Skip if already in graph
            if paper_id in nodes:
                logging.info(f'Paper {paper_id} is already in graph, continue')
                continue

            # Get paper citations
            citations = DataRetriever.get_citation_data(paper_id)
            if not citations:
                logging.info(f'Paper {paper_id} does not have any citations')

            # Add reversed edges to the graph for BFS
            citation_nodes = [cit['paperId']
                              for cit in citations if cit['paperId']]
            citation_edges = [(paper_id, cit['paperId'])
                              for cit in citations if cit['paperId']]

            # Add the node and incoming edges to the graph
            nodes.append(paper_id)
            graph.add_node(paper_id)
            graph.add_nodes_from(citation_nodes)
            graph.add_edges_from(citation_edges)

        node_groups.append(nodes)

    return graph, node_groups


def check_groups_not_empty(groups):
    group_sizes = [len(g) for g in groups]
    if 0 in group_sizes:
        empty_group = group_sizes.index(0) + 1
        raise EmptyGroupError(empty_group)


def get_crosschecked_nodes(graph, node_groups):
    crosschecked = set(graph.nodes)
    for group_nodes in node_groups:
        reachable = nx.bfs_layers(graph, group_nodes)

        try:
            next(reachable)  # skip group nodes in layer 0
            crosschecked &= set(next(reachable))
        except StopIteration:
            # No papers are reachable from one of the groups
            return []
    return list(crosschecked)


def crosscheck(groups):
    # Throw an error if one of the groups is empty
    check_groups_not_empty(groups)

    # Build the citation graph
    logging.info('Building the paper graph')
    graph, node_groups = build_graph(groups)

    # Throw an error if one of the groups is empty after paper retrieval
    check_groups_not_empty(node_groups)

    # Find nodes that are reachable from both sets
    logging.info('Looking for target papers')
    crosschecked = get_crosschecked_nodes(graph, node_groups)
    logging.info(f'Found {len(crosschecked)} papers')

    return crosschecked, node_groups
