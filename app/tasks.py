from celery import shared_task
from flask import render_template

from app.crosscheck import crosscheck


def extract_groups(form_data):
    group1 = [el.strip() for el in form_data['group1'].split('\n')]
    group2 = [el.strip() for el in form_data['group2'].split('\n')]
    return [group1, group2]


# Define the Celery task
@shared_task
def analyse(form_data):
    groups = extract_groups(form_data)
    data = crosscheck(groups)
    return render_template('response.html', paper_data=data)