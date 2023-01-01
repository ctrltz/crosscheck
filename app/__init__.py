# TODO: enable celery
from celery import Celery
from flask import Flask, request, make_response

from app.tasks import analyse

def create_app():
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
        CELERY_BROKER_URL='redis://localhost:6379/0',
        CELERY_BACKEND_URL='redis://localhost:6379/0'
    )

    # celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
    # celery.conf.update(app.config)

    # # Import and register Celery tasks
    # from app.tasks import tasks
    # tasks.init_app(app)

    # TODO: progress endpoint for a specific job

    # Main endpoint for initiating a request
    @app.route('/api/crosscheck', methods=['GET', 'POST'])
    def crosscheck():
        if request.method == 'POST':
            # Handle form submission
            form_data = request.form
            # TODO: run the task asynchronously and return job id
            result, return_code = analyse(form_data)
            response = make_response(result, return_code)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        return {'message': 'API endpoint of crosscheck.'}

    return app