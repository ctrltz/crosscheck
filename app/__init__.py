import os

from celery.result import AsyncResult
from flask import Flask, request, jsonify
from flask_cors import CORS

from app.celery import celery_app
from app.tasks import analyze


def create_app():
    # Create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        VERSION=os.environ.get('HEROKU_RELEASE_VERSION', 'local')
    )
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Main endpoint for initiating a request
    @app.route('/api/crosscheck', methods=['GET', 'POST'])
    def submit():
        if request.method == 'POST':
            # Handle form submission
            form_data = request.form
            task = analyze.delay(form_data)
            return jsonify({'task_id': task.id}), 202
        return {'message': 'API endpoint of crosscheck', 'version': app.config['VERSION']}

    # Endpoint for getting the result
    @app.route('/api/crosscheck/<task_id>', methods=['GET'])
    def retrieve(task_id):
        task_result = AsyncResult(task_id, app=celery_app)
        result = {
            "task_id": task_id,
            "task_status": task_result.state,
            "task_result": task_result.result
        }
        return jsonify(result), 200

    return app
