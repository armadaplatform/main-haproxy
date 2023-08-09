from __future__ import print_function

import re
import base64
import gzip
import logging
import os
import random
import shutil
import socket
import subprocess
import sys
import traceback
from functools import wraps
from datetime import datetime

import bottle
from armada import hermes
from bottle import request, response, HTTPError

sys.path.append('/opt/microservice/src')
from common.consul import consul_get

WELCOME_MESSAGE = '''Welcome to main-haproxy.
Did you mean to get here?
Perhaps your magellan is not properly configured or requested service is down.
'''

auth_config = hermes.get_config('auth_config.json', {})

STORE_STATS_FOR_DAYS = 7
STATS_PATH = '/tmp/stats'
AUTHORIZATION_TOKEN = auth_config.get('main_haproxy_auth_token')
RESTRICT_ACCESS = bool(AUTHORIZATION_TOKEN)


def _restrict_access(raw_token):
    unauthorized_error = HTTPError(401)
    try:
        match = re.match(r'Token (?P<token>\w+)', raw_token)
    except TypeError:
        raise unauthorized_error

    if match is None:
        raise unauthorized_error

    if match.group('token') != AUTHORIZATION_TOKEN:
        raise unauthorized_error


def authorize(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        try:
            if RESTRICT_ACCESS:
                _restrict_access(request.headers.get('Authorization'))
        except HTTPError as e:
            e.add_header('WWW-Authenticate', 'Token')
            return e
        else:
            return fun(*args, **kwargs)
    return wrapper


def _log_request():
    request_time = datetime.now()
    line = ' '.join(map(str, [
        request.remote_addr,
        request_time,
        request.method,
        request.url,
        response.status,
    ]))
    print(line, file=sys.stderr)


def _remove_old_stats():
    if random.randrange(100) > 0:
        return
    stats_dirs = os.listdir(STATS_PATH)
    now = datetime.now()
    for stats_dir in stats_dirs:
        try:
            stats_dir_date = datetime.strptime(stats_dir, '%Y-%m-%d')
        except ValueError:
            traceback.print_exc()
            continue
        if (now - stats_dir_date).total_seconds() > (86400 * STORE_STATS_FOR_DAYS):
            shutil.rmtree(os.path.join(STATS_PATH, stats_dir))


def _save_stats():
    cmd = 'echo "show stat" | socat unix-connect:/var/run/haproxy/stats.sock stdio'
    try:
        stats_csv = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        return
    now = datetime.now()
    stats_dir = os.path.join(STATS_PATH, now.date().isoformat())
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)
    stats_path = os.path.join(stats_dir, '{}.csv.gz'.format(now.strftime('%Y-%m-%dT%H_%M')))
    with gzip.open(stats_path, 'ab') as f:
        f.write(stats_csv)
    _remove_old_stats()


def _update_stats_endpoint():
    stats_enabled = subprocess.call('nc -z localhost 8001'.split()) == 0
    if stats_enabled:
        os.system('supervisorctl start register_stats')
    else:
        os.system('supervisorctl stop register_stats')
        service_id = '{}:stats'.format(socket.gethostname())
        consul_get('agent/service/deregister/{}'.format(service_id))


@bottle.route('/upload_config', method='POST')
@authorize
def upload_config():
    config_body = base64.b64decode(request.body.read())
    with open('/etc/haproxy/haproxy.cfg', 'wb') as haproxy_config_file:
        haproxy_config_file.write(config_body)
    try:
        _save_stats()
    except Exception:
        logging.warning('Saving haproxy stats failed:')
        traceback.print_exc()
    os.system('service haproxy reload')
    try:
        _update_stats_endpoint()
    except:
        logging.warning('Updating haproxy stats endpoint failed:')
        traceback.print_exc()


def _default_handler():
    response.status = 503
    response.content_type = 'text/plain'
    _log_request()
    return WELCOME_MESSAGE


@bottle.route('/')
def index():
    return _default_handler()


def main():
    error_codes = [404, 405, 503]
    for error_code in error_codes:
        bottle.error(error_code)(lambda error: _default_handler())
    bottle.run(quiet=True)


if __name__ == '__main__':
    main()
