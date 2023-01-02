import warnings

from celery import shared_task
from flask import render_template

from app.crosscheck import (crosscheck, EmptyGroupError, 
    PaperNotFoundWarning, CitationDiscrepancyWarning)
from app.preprocess import extract_groups


# Define the Celery task
@shared_task
def analyse(form_data):
    groups = extract_groups(form_data)
    result = {}
    return_code = 400

    with warnings.catch_warnings(record=True) as ws:
        # Run the analysis
        try:
            data, source_papers = crosscheck(groups)
            result['data'] = data
            result['source'] = source_papers
            return_code = 200
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

    return result, return_code
