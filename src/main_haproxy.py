from __future__ import print_function

import base64
import os
import sys
from datetime import datetime

import bottle
from bottle import request, response

WELCOME_MESSAGE = '''Welcome to main-haproxy.
Did you mean to get here?
Perhaps your magellan is not properly configured or requested service is down.
'''


def log_request():
    request_time = datetime.now()
    line = ' '.join(map(str, [
        request.remote_addr,
        request_time,
        request.method,
        request.url,
        response.status,
    ]))
    print(line, file=sys.stderr)


@bottle.route('/upload_config', method='POST')
def upload_config():
    config_body = base64.b64decode(request.body.read())
    with open('/etc/haproxy/haproxy.cfg', 'w') as haproxy_config_file:
        haproxy_config_file.write(config_body)
    os.system('service haproxy reload')


def default_handler():
    response.status = 503
    response.content_type = 'text/plain'
    log_request()
    return WELCOME_MESSAGE


@bottle.route('/')
def index():
    return default_handler()


def main():
    error_codes = [404, 405, 503]
    for error_code in error_codes:
        bottle.error(error_code)(lambda error: default_handler())
    bottle.run(quiet=True)


if __name__ == '__main__':
    main()
