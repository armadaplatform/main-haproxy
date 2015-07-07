import base64
import os

import web


class UploadConfig(object):
    def POST(self):
        config_body = base64.b64decode(web.data())
        with open('/etc/haproxy/haproxy.cfg', 'w') as haproxy_config_file:
            haproxy_config_file.write(config_body)
        os.system('service haproxy reload')


class Health(object):
    def GET(self):
        return 'ok'


class Index(object):
    def GET(self):
        web.ctx.status = '503 Service Unavailable'
        return ('Welcome to main-haproxy.\n'
                'Did you mean to get here?\n'
                'Perhaps your magellan is not properly configured or requested service is down.\n')


def main():
    urls = (
        '/upload_config', UploadConfig.__name__,
        '/health', Health.__name__,
        '/', Index.__name__,
    )
    app = web.application(urls, globals())
    app.run()


if __name__ == '__main__':
    main()
