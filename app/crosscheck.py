import networkx as nx
import requests


PAPER_URL = 'https://api.semanticscholar.org/graph/v1/paper/{0}?fields={1}'
PAPER_CITATION_FIELDS = 'citationCount,citations.paperId,citations.citationCount,' + \
    'citations.title,citations.url,citations.authors,citations.journal,citations.year'
CITATIONS_URL = 'https://api.semanticscholar.org/graph/v1/paper/{0}/citations?fields={1}&offset={2}&limit={3}'
CITATIONS_FIELDS = 'paperId,url,title,citationCount,authors,journal,year'
MAX_LIMIT = 1000
MAX_TOTAL_COUNT = 10000


def get_paper_data(doi, fields):
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
                print(f'Failed to find paper: {paper_doi}')
                continue

            citations = paper_data.get('citations', [])
            num_cit_retrieved = len(citations)
            num_cit_total = paper_data['citationCount']
            print(paper_doi)
            print(f'Retrieved {num_cit_retrieved} / {num_cit_total} citations')
            while num_cit_retrieved < num_cit_total:
                new_citations = get_citation_data(paper_doi, CITATIONS_FIELDS, num_cit_retrieved)
                citations.extend([cit['citingPaper'] for cit in new_citations.get('data', [])])
                num_cit_retrieved = new_citations.get('next', None)
                if num_cit_retrieved:
                    assert len(citations) == num_cit_retrieved, paper_doi
                else:
                    assert len(citations) == num_cit_total, paper_doi
                    num_cit_retrieved = num_cit_total
                print(f'Retrieved {num_cit_retrieved} / {num_cit_total} citations')

            # Add reversed edges to the graph for BFS
            citation_nodes = [(cit['paperId'], 
                              dict(citationCount=cit['citationCount'],
                                   url=cit['url'], title=cit['title'],
                                   year=cit.get('year', ''), 
                                   authors=authors_compact(cit.get('authors', [])),
                                   journal=journal_compact(cit.get('journal', {}))))
                              for cit in citations
                              if cit['paperId']]
            citation_edges = [(paper_id, cit['paperId']) 
                              for cit in citations
                              if cit['paperId']]  # skip None?

            # Add the node and incoming edges to the graph
            nodes.append(paper_id)
            graph.add_node(paper_id, citationCount=num_cit_total)            
            graph.add_nodes_from(citation_nodes)
            graph.add_edges_from(citation_edges)

        node_groups.append(nodes)

    return graph, node_groups


def crosscheck(groups):
    # Build the citation graph
    graph, node_groups = build_graph(groups)

    # Find nodes that are reachable from both sets
    crosschecked = set(graph.nodes)
    for group_nodes in node_groups:
        reachable = nx.bfs_layers(graph, group_nodes)
        print(next(reachable))  # skip group nodes in layer 0
        crosschecked &= set(next(reachable))

    crosschecked_data = [dict(paperId=n[0], **n[1]) 
                         for n in graph.nodes(data=True)
                         if n[0] in crosschecked]

    return crosschecked_data
