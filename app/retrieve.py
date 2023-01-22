import os
import requests
import warnings


BASE_URL = 'https://partner.semanticscholar.org/graph/v1'
MAX_CITATIONS = 10000
MAX_LIMIT = 1000
CITATION_FIELDS = ['paperId']
PAPER_FIELDS = ['paperId', 'url', 'title',
                'citationCount', 'authors', 'journal', 'year']


class PaperNotFoundWarning(Warning):
    pass


def authors_compact(authors):
    if not authors:
        return ''
    if len(authors) < 3:
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


def reformat(data):
    if 'year' not in data:
        data['year'] = ''
    data['authors'] = authors_compact(data.get('authors', []))
    data['journal'] = journal_compact(data.get('journal', {}))
    return data


class DataRetriever:
    def __init__(self) -> None:
        api_key = os.environ.get('SS_API_KEY', None)
        self.auth_header = None
        if api_key:
            self.auth_header = {'x-api-key': api_key}

    def papers_url(self, fields):
        uri = f"{BASE_URL}/paper/batch?fields={','.join(fields)}"

        return uri

    # TODO: add test on more than 10000 citations
    def paper_citations_url(self, paper_id, fields, offset=None, limit=MAX_LIMIT):
        if offset + limit >= MAX_CITATIONS:
            limit = MAX_CITATIONS - offset - 1

        uri = f"{BASE_URL}/paper/{paper_id}/citations/?fields={','.join(fields)}"
        if offset:
            uri += f'offset={offset}'
        if limit:
            uri += f'limit={limit}'

        return self._get(uri).json()

    def get_paper_data(self, paper_ids, fields):
        url = self.papers_url(paper_ids, fields)

        response = self._post(url, {'ids': paper_ids})

        data = response.json()
        return reformat(data)

    # TODO: add test on more than 1000 citations
    def get_citation_data(self, paper_id, fields=CITATION_FIELDS):
        offset = 0
        citations = []

        while offset is not None:
            url = self.paper_citations_url(paper_id, fields, offset)

            response = self._get(url)
            if response.status_code == 404:
                warnings.warn(paper_id, PaperNotFoundWarning)
                return [], False

            result = response.json()
            citations.extend([cit['citingPaper']
                             for cit in result.get('data', [])])
            offset = result.get('next', None)

        return citations, True

    def _get(self, url):
        return requests.get(url, headers=self.auth_header)

    def _post(self, url, data):
        return requests.post(url, data=data, headers=self.auth_header)
