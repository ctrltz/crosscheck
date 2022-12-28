from celery import Celery
from flask import Flask, request, make_response

from app.tasks import analyse

def create_app():
    # create and configure the app
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

    # a simple page that says hello
    @app.route('/api/crosscheck', methods=['GET', 'POST'])
    def crosscheck():
        if request.method == 'POST':
            # Handle form submission
            form_data = request.form
            response = make_response(analyse(form_data))
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        return {'message': 'API endpoint of crosscheck.'}

    return app