import pytest

from app.retrieve import authors_compact, journal_compact


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
