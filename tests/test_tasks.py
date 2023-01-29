from redis.client import Pipeline
from unittest.mock import DEFAULT, patch, call

from app.crosscheck import EmptyGroupError
from app.redis import RedisPapers, RedisRequests
from app.retrieve import DataRetriever, PaperNotFoundWarning
from app.tasks import analyze


@patch.object(DataRetriever, 'get_papers_batch', return_value=[])
@patch('app.crosscheck.crosscheck', side_effect=EmptyGroupError(1))
@patch.multiple(Pipeline, hincrby=DEFAULT, execute=DEFAULT)
def test_update_stats_failed_empty(mock_crosscheck, mock_retriever, **kwargs):
    analyze({'group1': 'aaaa\nbbbb', 'group2': 'bbb\nccc'})
    assert kwargs['hincrby'].has_calls(call(RedisRequests.HASH, RedisRequests.KEY_FAILED_EMPTY, 1))


@patch.object(DataRetriever, 'get_papers_batch', return_value=[])
@patch('app.crosscheck.crosscheck', side_effect=KeyError(1))
@patch.multiple(Pipeline, hincrby=DEFAULT, execute=DEFAULT)
def test_update_stats_failed_other(mock_crosscheck, mock_retriever, **kwargs):
    analyze({'group1': 'aaaa\nbbbb', 'group2': 'bbb\nccc'})
    assert kwargs['hincrby'].has_calls(call(RedisRequests.HASH, RedisRequests.KEY_FAILED_OTHER, 1))


@patch.object(DataRetriever, 'get_papers_batch', return_value=[])
@patch('app.crosscheck.crosscheck', return_value=[[1, 2, 3, 4], [5, 6]])
@patch.multiple(Pipeline, hincrby=DEFAULT, execute=DEFAULT)
def test_update_stats_completed(mock_crosscheck, mock_retriever, **kwargs):
    analyze({'group1': 'aaaa\nbbbb', 'group2': 'bbb\nccc'})
    assert kwargs['hincrby'].has_calls(call(RedisRequests.HASH, RedisRequests.KEY_COMPLETED, 1))
    assert kwargs['hincrby'].has_calls(call(RedisPapers.HASH, RedisPapers.KEY_PROCESSED, 2))


@patch.object(DataRetriever, 'get_papers_batch', return_value=[])
@patch('app.crosscheck.crosscheck', return_value=[[1, 2, 3, 4], [5, 6]],
       side_effect=PaperNotFoundWarning(7))
@patch.multiple(Pipeline, hincrby=DEFAULT, execute=DEFAULT)
def test_update_stats_paper_not_found(mock_crosscheck, mock_retriever, **kwargs):
    analyze({'group1': 'aaaa\nbbbb', 'group2': 'bbb\nccc'})
    assert kwargs['hincrby'].has_calls(call(RedisRequests.HASH, RedisRequests.KEY_COMPLETED, 1))
    assert kwargs['hincrby'].has_calls(call(RedisPapers.HASH, RedisPapers.KEY_PROCESSED, 2))
    assert kwargs['hincrby'].has_calls(call(RedisPapers.HASH, RedisPapers.KEY_NOT_FOUND, 1))
