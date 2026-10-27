import datetime


def health():
    return {'status': 'ok', 'timestamp': str(datetime.datetime.now())}


def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
