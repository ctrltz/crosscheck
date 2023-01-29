import logging
import os
import requests
import warnings


BASE_URL = 'https://partner.semanticscholar.org/graph/v1'
MAX_CITATIONS = 10000
MAX_LIMIT = 1000
CITATION_FIELDS = ['paperId']
PAPER_FIELDS = ['paperId', 'url', 'title',
                'citationCount', 'authors', 'journal', 'year']
SS_API_KEY = os.environ.get('SS_API_KEY', None)
AUTH_HEADER = None
if SS_API_KEY:
    AUTH_HEADER = {'x-api-key': SS_API_KEY}


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
    @staticmethod
    def paper_url(paper_id, fields):
        uri = f"{BASE_URL}/paper/{paper_id}?fields={','.join(fields)}"

        return uri

    @staticmethod
    def papers_url(fields):
        uri = f"{BASE_URL}/paper/batch?fields={','.join(fields)}"

        return uri

    @staticmethod
    def paper_citations_url(paper_id, fields, offset=None):
        limit = MAX_LIMIT
        if offset + limit >= MAX_CITATIONS:
            limit = MAX_CITATIONS - offset - 1

        uri = f"{BASE_URL}/paper/{paper_id}/citations?fields={','.join(fields)}"
        if offset:
            uri += f'&offset={offset}'
        if limit:
            uri += f'&limit={limit}'

        return uri

    @classmethod
    def get_paper_data(cls, paper_id, fields=PAPER_FIELDS):
        logging.info(f'Get paper data: {paper_id} | {len(fields)} field(s)')
        url = cls.paper_url(paper_id, fields)

        response = cls._get(url)
        if response.status_code == 404:
            logging.warn(f'404 {paper_id} not found')
            warnings.warn(paper_id, PaperNotFoundWarning)
            return {}
        logging.info(f'{response.status_code} {url}')

        return response.json()

    @classmethod
    def get_papers_batch(cls, paper_ids, fields=PAPER_FIELDS):
        logging.info(f'Get papers batch: {len(paper_ids)} | {len(fields)} field(s)')
        url = cls.papers_url(fields)

        papers = []
        n_total = len(paper_ids)
        n_batches = 1 + (n_total - 1) // MAX_LIMIT
        logging.info(f'{n_total} papers in total, splitting into batches of {MAX_LIMIT}')
        for i in range(n_batches):
            s = i * MAX_LIMIT
            e = min((i + 1) * MAX_LIMIT, n_total)
            batch_ids = paper_ids[s:e]
            batch_size = len(batch_ids)
            logging.info(f'Batch {i + 1} | {batch_size} papers')
            response = cls._post(url, data={'ids': batch_ids})

            data = response.json()
            papers.extend([reformat(paper_data) for paper_data in data])

        return papers

    @classmethod
    def get_citation_data(cls, paper_id, fields=CITATION_FIELDS):
        logging.info(f'Get paper citations: {paper_id} | {len(fields)} field(s)')
        offset = 0
        citations = []

        while offset is not None:
            url = cls.paper_citations_url(paper_id, fields, offset)

            response = cls._get(url)
            if response.status_code == 404:
                warnings.warn(paper_id, PaperNotFoundWarning)
                return []

            result = response.json()
            citations.extend([cit['citingPaper']
                             for cit in result.get('data', [])])
            offset = result.get('next', None)

        return citations

    @staticmethod
    def _get(url):
        logging.info(f'GET {url}')
        return requests.get(url, headers=AUTH_HEADER)

    @staticmethod
    def _post(url, data):
        logging.info(f"POST {url} | {len(data['ids'])} papers")
        return requests.post(url, json=data, headers=AUTH_HEADER)
