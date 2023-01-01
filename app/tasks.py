import warnings

from celery import shared_task
from flask import render_template

from app.crosscheck import (crosscheck, EmptyGroupError, 
    PaperNotFoundWarning, CitationDiscrepancyWarning)


def extract_groups(form_data):
    # TODO: refine supported ID types, throw error if one of the groups is empty
    group1 = [el.strip() for el in form_data['group1'].split('\n')]
    group2 = [el.strip() for el in form_data['group2'].split('\n')]
    return [group1, group2]


# Define the Celery task
@shared_task
def analyse(form_data):
    groups = extract_groups(form_data)
    result = {}
    return_code = 400

    with warnings.catch_warnings(record=True) as ws:
        # Run the analysis
        try:
            data = crosscheck(groups)
            result['data'] = render_template('response.html', paper_data=data)
            return_code = 200
        except EmptyGroupError as e:
            result['error'] = {'message': str(e), 'category': 'EmptyGroupError'}
        except Exception as e:
            # Wrap unprocessed exceptions
            result['error'] = {'message': [], 'category': 'ServerError'}

        # Add warnings that occurred along the way
        messages = []
        for w in ws:
            if issubclass(w.category, (PaperNotFoundWarning, CitationDiscrepancyWarning)):
                messages.append({'message': str(w.message), 'category': w.category.__name__})
            else:
                print(f'Unhandled warning: {str(w)}')
        result['messages'] = messages
    
    print(return_code)
    print(result)

    return result, return_code
