import networkx as nx
import requests
import warnings


PAPER_URL = 'https://api.semanticscholar.org/graph/v1/paper/{0}?fields={1}'
PAPER_CITATION_FIELDS = 'url,title,citationCount,authors,journal,year,citations.citationCount,' + \
    'citations.title,citations.url,citations.authors,citations.journal,citations.year'
CITATIONS_URL = 'https://api.semanticscholar.org/graph/v1/paper/{0}/citations?fields={1}&offset={2}&limit={3}'
CITATIONS_FIELDS = 'paperId,url,title,citationCount,authors,journal,year'
MAX_LIMIT = 1000
MAX_TOTAL_COUNT = 10000
# TODO: think about overall limits on the amount of papers to be processed


# TODO: throw error only if two groups are empty?
class EmptyGroupError(Exception):
    pass


class PaperNotFoundWarning(Warning):
    pass


class CitationDiscrepancyWarning(Warning):
    pass


def get_paper_data(doi, fields):
    # TODO: handle situation if API is not available or paper is not found
    return requests.get(PAPER_URL.format(doi, fields)).json()


def get_citation_data(doi, fields, offset, limit=MAX_LIMIT):
    if offset + limit >= MAX_TOTAL_COUNT:
        limit = MAX_TOTAL_COUNT - offset - 1
    return requests.get(CITATIONS_URL.format(doi, fields, offset, limit)).json()


def authors_compact(authors):
    if not authors:
        return ''
    if len(authors) <= 3:
        return ', '.join([a['name'] for a in authors])
    else:
        return f"{authors[0]['name']} et al."


def journal_compact(journal):
    if not journal or not journal.get('name', ''):
        return ''
    result = journal['name']
    if 'volume' in journal:
        result += f" {journal['volume']}"
    if 'pages' in journal:
        result += f":{journal['pages']}"
    return result


def node_metadata(data):
    return dict(citationCount=data['citationCount'],
                url=data['url'],
                title=data['title'],
                year=data.get('year', ''), 
                authors=authors_compact(data.get('authors', [])),
                journal=journal_compact(data.get('journal', {})))


# TODO: add test on more than 1000 citations
# TODO: decouple paper info from plain citation info, paper info can be loaded later via POST endpoint
def build_graph(groups):
    graph = nx.DiGraph()
    node_groups = []

    for group_papers in groups:
        nodes = []
        for paper_doi in group_papers:
            # Get paper data
            paper_data = get_paper_data(paper_doi, PAPER_CITATION_FIELDS)
            paper_id = paper_data.get('paperId', None)
            if not paper_id:
                warnings.warn(paper_doi, PaperNotFoundWarning)
                continue

            citations = paper_data.get('citations', [])
            num_cit_expected = len(citations)
            num_cit_total = paper_data['citationCount']
            print(paper_doi)
            print(f'Retrieved {num_cit_expected} / {num_cit_total} citations')
            while num_cit_expected < num_cit_total:
                new_citations = get_citation_data(paper_doi, CITATIONS_FIELDS, num_cit_expected)
                citations.extend([cit['citingPaper'] for cit in new_citations.get('data', [])])
                num_cit_retrieved = new_citations.get('next', None)
                num_cit_expected = num_cit_retrieved or num_cit_total
                num_cit_actual = len(citations)
                if num_cit_actual != num_cit_expected:
                    warnings.warn(paper_doi, CitationDiscrepancyWarning)
                print(f'Retrieved {num_cit_actual} / {num_cit_total} citations')

            # Add reversed edges to the graph for BFS
            citation_nodes = [(cit['paperId'], node_metadata(cit))
                              for cit in citations
                              if cit['paperId']]
            citation_edges = [(paper_id, cit['paperId']) 
                              for cit in citations
                              if cit['paperId']]  # skip None?

            # Add the node and incoming edges to the graph
            nodes.append(paper_id)
            graph.add_node(paper_id, **node_metadata(paper_data))            
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
        
        # TODO: add test on when no papers are reachable from one of the groups
        try:
            print(next(reachable))  # skip group nodes in layer 0
            crosschecked &= set(next(reachable))
        except StopIteration:
            # No papers are reachable from one of the groups
            return []
    return crosschecked


def crosscheck(groups):
    # Throw an error if one of the groups is empty
    # TODO: add test
    check_groups_not_empty(groups)

    # Build the citation graph
    graph, node_groups = build_graph(groups)

    # Throw an error if one of the groups is empty after paper retrieval
    # TODO: add test
    check_groups_not_empty(node_groups)

    # Find nodes that are reachable from both sets
    crosschecked = get_crosschecked_nodes(graph, node_groups)

    crosschecked_data = [dict(paperId=n[0], **n[1])
                         for n in graph.nodes(data=True)
                         if n[0] in crosschecked]

    source_data = [dict(paperId=n[0], **n[1])
                   for n in graph.nodes(data=True)
                   if any([n[0] in ng for ng in node_groups])]

    return crosschecked_data, source_data
