import pytest

from app.preprocess import extract_paper_ids, process_line


@pytest.mark.parametrize("test_input,expected", [
    ('pubmed.ncbi.nlm.nih.gov/1234/', 'PMID:1234'),
    ('https://pubmed.ncbi.nlm.nih.gov/12345678/', 'PMID:12345678'),
    ('doi:10.20/aaa.30.bbb.40', 'DOI:10.20/aaa.30.bbb.40'),
    ('doi: 10.20/aaa.30.bbb.40', 'DOI:10.20/aaa.30.bbb.40'),
    ('               doi: 10.20/aaa.30.bbb.40       ', 'DOI:10.20/aaa.30.bbb.40'),
    ('DOI: 10.20/aaa.30.bbb.40', 'DOI:10.20/aaa.30.bbb.40'),
    ('doi.org/10.20/aaa.30.bbb.40', 'DOI:10.20/aaa.30.bbb.40'),
    ('dx.doi.org/10.20/aaa.30.bbb.40', 'DOI:10.20/aaa.30.bbb.40'),
    ('https://dx.doi.org/10.20/aaa.30.bbb.40', 'DOI:10.20/aaa.30.bbb.40'),
    ('https://www.semanticscholar.org/paper/9298bc29443bdfe48bed12456fabd3e8e7af03ed',
     '9298bc29443bdfe48bed12456fabd3e8e7af03ed'),
    ('aaaa', 'aaaa')
])
def test_process_line(test_input, expected):
    assert process_line(test_input) == expected


@pytest.mark.parametrize("test_input,expected", [
    ('aaa\n\nbbb', ['aaa', 'bbb'])
])
def test_extract_paper_ids(test_input, expected):
    assert extract_paper_ids(test_input) == expected
