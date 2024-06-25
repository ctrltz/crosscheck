import networkx as nx
import pytest

from unittest.mock import patch

from crosscheck.crosscheck import EmptyGroupError, build_graph, check_groups_not_empty, crosscheck, get_crosschecked_nodes
from crosscheck.retrieve import DataRetriever


@pytest.mark.parametrize('test_input,expected', [
    ([[]], '1'),
    ([['aaa'], []], '2')
])
def test_check_groups_not_empty_throws(test_input, expected):
    with pytest.raises(EmptyGroupError) as exc_info:
        check_groups_not_empty(test_input)
    assert str(exc_info.value) == expected


def test_check_groups_not_empty():
    check_groups_not_empty([['aaa'], ['bbb']])


def test_crosscheck_throws_on_empty_group_original():
    with pytest.raises(EmptyGroupError) as exc_info:
        crosscheck([['aaa'], []])
    assert str(exc_info.value) == '2'


def test_crosscheck_throws_on_empty_group_after_graph_is_built():
    with pytest.raises(EmptyGroupError) as exc_info:
        with patch('crosscheck.retrieve.DataRetriever.get_paper_data', 
                   return_value=[]):
            assert not DataRetriever.get_paper_data('aaa')
            crosscheck([['aaa'], ['bbb']])
    assert str(exc_info.value) == '1'


@patch.object(DataRetriever, 'get_citation_data',
              return_value=[{'paperId': 'bbb'}, {'paperId': 'ccc'}])
@patch.object(DataRetriever, 'get_paper_data', return_value={'paperId': 'aaa'})
def test_build_graph(mock1, mock2):
    graph, node_groups = build_graph([['aaa']])
    assert graph.number_of_nodes() == 3
    assert graph.number_of_edges() == 2
    assert graph.has_edge('aaa', 'bbb')
    assert graph.has_edge('aaa', 'ccc')
    assert node_groups == [['aaa']]
    mock1.assert_called_once()
    mock2.assert_called_once()


@pytest.mark.parametrize('name,edge_list,node_groups,expected', [
    ('1common', [(1, 3), (1, 4), (2, 4), (2, 5)], [[1], [2]], [4]),
    ('1group_not_reachable', {1: [3, 4], 2: []}, [[1], [2]], []),
    ('cocitation_within_groups', [(1, 5), (2, 5),
     (3, 6), (4, 6)], [[1, 2], [3, 4]], []),
    ('cocitation_between_groups', [
     (1, 5), (3, 5), (2, 6), (4, 6)], [[1, 2], [3, 4]], [5, 6])
])
def test_get_crosschecked_nodes(name, edge_list, node_groups, expected):
    g = nx.DiGraph(edge_list)
    assert get_crosschecked_nodes(g, node_groups) == expected, name
