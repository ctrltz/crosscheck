import re

PUBMED_URL = re.compile(r"pubmed\.ncbi\.nlm\.nih\.gov\/(?P<id>\d+)\/")
DOI_PREFIX = re.compile(r"(?:doi|DOI):\s?(?P<id>.*)")
DOI_URL = re.compile(r"doi\.org\/(?P<id>.*)")
SEMANTIC_SCHOLAR_URL = re.compile(r"semanticscholar\.org\/paper\/(?P<id>.*)")
URL_PATTERNS = {
    PUBMED_URL: 'PMID:{0}',
    DOI_PREFIX: 'DOI:{0}',
    DOI_URL: 'DOI:{0}',
    SEMANTIC_SCHOLAR_URL: '{0}'
}


def process_line(line):
    """
    Extract identifiers from DOI, Pubmed, and Semantic Scholar links.
    If no match is found, leave the input as is
    """
    line = line.strip()
    for pattern, id_template in URL_PATTERNS.items():
        match = pattern.search(line)
        if match:
            return id_template.format(match.group('id'))

    return line


def extract_paper_ids(data):
    return [process_line(el) for el in data.split('\n') if el]


def extract_groups(form_data):
    group1 = extract_paper_ids(form_data['group1'])
    group2 = extract_paper_ids(form_data['group2'])
    return [group1, group2]
