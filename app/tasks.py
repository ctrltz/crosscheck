import logging
import warnings

from app.celery import celery_app
from app.crosscheck import (crosscheck, EmptyGroupError)
from app.preprocess import extract_groups
from app.retrieve import DataRetriever, PaperNotFoundWarning


# Define the Celery task
@celery_app.task(name="analyze")
def analyze(form_data):
    groups = extract_groups(form_data)
    result = {}

    with warnings.catch_warnings(record=True) as ws:
        try:
            # Run the analysis
            crosschecked, sources = crosscheck(groups)
            source_papers = []
            for g in sources:
                source_papers.extend(g)

            # Retrieve information about the papers
            dr = DataRetriever()
            crosschecked_data = dr.get_paper_data(crosschecked)
            source_data = dr.get_paper_data(source_papers)

            # Pack the results
            result['data'] = crosschecked_data
            result['source'] = source_data
        except EmptyGroupError as e:
            result['error'] = {'message': str(e), 'category': 'EmptyGroupError'}
        except Exception as e:
            # Wrap unprocessed exceptions
            logging.error(str(e))
            result['error'] = {'message': [], 'category': 'ServerError'}

        # Add warnings that occurred along the way
        messages = []
        for w in ws:
            if issubclass(w.category, (PaperNotFoundWarning)):
                messages.append({'message': str(w.message), 'category': w.category.__name__})
            else:
                print(f'Unhandled warning: {str(w)}')
        result['messages'] = messages

    return result
