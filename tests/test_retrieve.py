import pytest
import requests

from unittest.mock import patch

from crosscheck.retrieve import DataRetriever, authors_compact, journal_compact
from tests.utils import MockResponse


@pytest.mark.parametrize('test_input,expected', [
    ([], ''),
    ([{'name': 'A. Author'}], 'A. Author'),
    ([{'name': 'A. Author'}, {'name': 'B. Author'}], 'A. Author, B. Author'),
    ([{'name': 'A. Author'}, {'name': 'B. Author'}, {'name': 'C. Author'}], 'A. Author et al.')
])
def test_authors_compact(test_input, expected):
    assert authors_compact(test_input) == expected


@pytest.mark.parametrize('test_input,expected', [
    ({}, ''),
    ({'name': 'Journal'}, 'Journal'),
    ({'name': 'Journal', 'pages': '1-2'}, 'Journal'),
    ({'name': 'Journal', 'volume': '12'}, 'Journal 12'),
    ({'name': 'Journal', 'volume': '12', 'pages': '1-2'}, 'Journal 12:1-2')
])
def test_journal_compact(test_input, expected):
    assert journal_compact(test_input) == expected


@pytest.mark.parametrize('paper_id,fields,expected', [
    ('aaa', ['paperId'], '/aaa?fields=paperId'),
    ('bbb', ['paperId', 'year', 'title', 'authors'], '/bbb?fields=paperId,year,title,authors'),
])
def test_dataretriever_paper_url(paper_id, fields, expected):
    assert expected in DataRetriever.paper_url(paper_id, fields)


@pytest.mark.parametrize('fields,expected', [
    (['paperId'], '/batch?fields=paperId'),
    (['paperId', 'year', 'title', 'authors'], '/batch?fields=paperId,year,title,authors'),
])
def test_dataretriever_papers_url(fields, expected):
    assert expected in DataRetriever.papers_url(fields)


@pytest.mark.parametrize('paper_id,fields,offset,expected', [
    ('aaa', ['paperId'], 0, '/paper/aaa/citations?fields=paperId&limit=1000'),
    ('bbb', ['paperId', 'year'], 1000, '/paper/bbb/citations?fields=paperId,year&offset=1000&limit=1000'),
    ('ccc', ['paperId'], 9200, '/paper/ccc/citations?fields=paperId&offset=9200&limit=799'),
])
def test_dataretriever_paper_citations_url(paper_id, fields, offset, expected):
    assert expected in DataRetriever.paper_citations_url(paper_id, fields, offset)


@patch.object(requests, 'get')
def test_dataretriever_get_citation_data(mock):
    citation_data = [
        {'offset': 0, 'next': 1000, 'data': [{'citingPaper': {'paperId': 'aaa'}}]},
        {'offset': 1000, 'next': 2000, 'data': [{'citingPaper': {'paperId': 'bbb'}}]},
        {'offset': 2000, 'data': [{'citingPaper': {'paperId': 'ccc'}}]},
    ]
    mock.side_effect = [MockResponse(cit, 200) for cit in citation_data]
    citations = DataRetriever.get_citation_data('aaa')
    assert len(citations) == 3
    assert [cit['paperId'] for cit in citations] == ['aaa', 'bbb', 'ccc']
    assert mock.call_count == 3


@patch.object(requests, 'post')
def test_dataretriever_get_papers_batch(mock):
    paper_data = [
        [{'paperId': 'aaa', 'authors': [{'name': 'A. Author'}]}],
        [{'paperId': 'bbb', 'journal': {'name': 'Journal'}}],
        [{'paperId': 'ccc', 'year': 1234}],
    ]
    mock.side_effect = [MockResponse(pd, 200) for pd in paper_data]
    papers = DataRetriever.get_papers_batch(list(range(1, 3000)))
    assert len(papers) == 3
    assert [p['paperId'] for p in papers] == ['aaa', 'bbb', 'ccc']
    assert [p['authors'] for p in papers] == ['A. Author', '', '']
    assert [p['journal'] for p in papers] == ['', 'Journal', '']
    assert [p['year'] for p in papers] == ['', '', 1234]
    assert mock.call_count == 3
