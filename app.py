import logging
import os

from flask import Flask, jsonify, make_response, redirect, request
from flask_jwt_extended import JWTManager
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
from os import environ as env

from utils.log import Logger
from utils.redis_db import Redis
from api_routes import admin, user

load_dotenv(dotenv_path="conf/metabank.env")

# init Flask application
app = Flask(__name__)
app.secret_key = env['APP_SECRET_KEY']
app.url_map.strict_slashes = False
# app.config['DEBUG'] = True

# init JWT settings
app.config['JWT_SECRET_KEY'] = env['JWT_SECRET_KEY']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(env['JWT_ACCESS_TOKEN_EXPIRES'])
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(env['JWT_REFRESH_TOKEN_EXPIRES'])
app.config['JWT_HEADER_NAME'] = env['JWT_HEADER_NAME']
app.config['JWT_HEADER_TYPE'] = env['JWT_HEADER_TYPE']  # no need to add "Bearer ", only the JWT token itself
jwt = JWTManager(app)


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    try:
        redis = Redis()
        redis_connection = redis.get_connection()
        if redis_connection is False:
            return False
        token_in_redis = redis_connection.get(jti)
        return token_in_redis is not None
    except (ConnectionRefusedError, ConnectionError):
        return False


# init Mail settings
app.config['MAIL_SERVER'] = env['EMAIL_SMTP_SERVER']
app.config['MAIL_PORT'] = int(env['EMAIL_SMTP_PORT'])
app.config['MAIL_USERNAME'] = env['EMAIL_ADDRESS']
app.config['MAIL_PASSWORD'] = env['EMAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = env['EMAIL_TLS']

admin.add_routes(app)
user.add_routes(app)

# init logger
log_level = int(env['LOG_LEVEL'])
if log_level == 1:
    level = logging.DEBUG
elif log_level == 2:
    level = logging.INFO
elif log_level == 3:
    level = logging.WARNING
elif log_level == 4:
    level = logging.ERROR
elif log_level == 5:
    level = logging.CRITICAL
else:
    level = logging.WARNING

logger = logging.getLogger()
logger.setLevel(level)

# rotating file handler
log_formatter = logging.Formatter("[%(levelname)-8.8s] %(asctime)s [%(threadName)-12.12s] [%(name)-12.12s] %(message)s")
try:
    file_handler = TimedRotatingFileHandler(filename="{0}{1}".format(env['LOG_DIRECTORY'], env['LOG_FILE_NAME']),
                                            when='midnight', backupCount=int(env['LOG_NB_FILE']))
except FileNotFoundError as e:
    log_path = env['LOG_DIRECTORY']
    split_path = log_path.split(os.sep)
    current_directory = os.getcwd()
    for directory in split_path:
        if len(directory) > 0:
            current_directory = os.path.join(current_directory, directory)
            try:
                os.mkdir(path=current_directory)
            except FileExistsError:
                pass

    file_handler = TimedRotatingFileHandler(filename="{0}{1}".format(env['LOG_DIRECTORY'], env['LOG_FILE_NAME']),
                                            when='midnight', backupCount=int(env['LOG_NB_FILE']))

file_handler.setFormatter(log_formatter)
file_handler.setLevel(level)
logger.addHandler(file_handler)


# Override the response for expired jwt token
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_data):
    return make_response(jsonify({'status': False, 'message': 'The JWT token expired'}), 401)


# Override the response for invalid jwt token
@jwt.invalid_token_loader
def my_invalid_token_callback(invalid_token):
    return make_response(jsonify({'status': False, 'message': 'The token is invalid: {}'.format(invalid_token)}), 401)


@app.before_request
def clear_trailing():
    """
    Decorator to check if there is a slash at the end of the requested url, and remove it to prevent 404 http error
    :return:
    """
    rp = request.path
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])


if __name__ == '__main__':
    app.logger = Logger()
    app.run(host='0.0.0.0', port=int(env['APP_PORT']), debug=False)
