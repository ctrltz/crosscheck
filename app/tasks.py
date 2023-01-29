import logging
import warnings

from app.celery import celery_app
from app.crosscheck import (crosscheck, EmptyGroupError)
from app.preprocess import extract_groups
from app.redis import RedisPapers, RedisRequests, redis_app
from app.retrieve import DataRetriever, PaperNotFoundWarning


# Define the Celery task
@celery_app.task(name="analyze")
def analyze(form_data):
    groups = extract_groups(form_data)
    result = {}
    r = redis_app.pipeline()

    with warnings.catch_warnings(record=True) as ws:
        try:
            # Run the analysis
            logging.info('Starting crosscheck')
            crosschecked, sources = crosscheck(groups)
            source_papers = []
            for g in sources:
                source_papers.extend(g)

            # Retrieve information about the papers
            logging.info('Retrieving data about crosschecked papers')
            crosschecked_data = DataRetriever.get_papers_batch(crosschecked)
            logging.info('Retrieving data about source papers')
            source_data = DataRetriever.get_papers_batch(source_papers)

            # Pack the results
            result['data'] = crosschecked_data
            result['source'] = source_data
            r.hincrby(RedisRequests.HASH, RedisRequests.KEY_COMPLETED, 1)
            r.hincrby(RedisPapers.HASH, RedisPapers.KEY_PROCESSED, len(source_papers))
        except EmptyGroupError as e:
            result['error'] = {'message': str(e), 'category': 'EmptyGroupError'}
            r.hincrby(RedisRequests.HASH, RedisRequests.KEY_FAILED_EMPTY, 1)
        except Exception as e:
            # Wrap unprocessed exceptions
            logging.error(f'Exception caught: {str(e)}')
            result['error'] = {'message': [], 'category': 'ServerError'}
            r.hincrby(RedisRequests.HASH, RedisRequests.KEY_FAILED_OTHER, 1)

        # Add warnings that occurred along the way
        messages = []
        for w in ws:
            if issubclass(w.category, (PaperNotFoundWarning)):
                messages.append({'message': str(w.message), 'category': w.category.__name__})
                r.hincrby(RedisPapers.HASH, RedisPapers.KEY_NOT_FOUND, 1)
            else:
                print(f'Unhandled warning: {str(w)}')
        result['messages'] = messages

    r.hincrby(RedisRequests.HASH, RedisRequests.KEY_TOTAL, 1)
    r.execute()
    return result
