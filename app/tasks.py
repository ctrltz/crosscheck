import warnings

from app.celery import celery_app
from app.crosscheck import (crosscheck, EmptyGroupError, 
    PaperNotFoundWarning, CitationDiscrepancyWarning)
from app.preprocess import extract_groups


# Define the Celery task
@celery_app.task(name="analyze")
def analyze(form_data):
    groups = extract_groups(form_data)
    result = {}

    with warnings.catch_warnings(record=True) as ws:
        # Run the analysis
        try:
            data, source_papers = crosscheck(groups)
            result['data'] = data
            result['source'] = source_papers
        except EmptyGroupError as e:
            result['error'] = {'message': str(e), 'category': 'EmptyGroupError'}
        except Exception as e:
            # Wrap unprocessed exceptions
            print(str(e))
            result['error'] = {'message': [], 'category': 'ServerError'}

        # Add warnings that occurred along the way
        messages = []
        for w in ws:
            if issubclass(w.category, (PaperNotFoundWarning, CitationDiscrepancyWarning)):
                messages.append({'message': str(w.message), 'category': w.category.__name__})
            else:
                print(f'Unhandled warning: {str(w)}')
        result['messages'] = messages

    return result
