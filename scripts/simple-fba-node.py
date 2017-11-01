import threading
import requests
import urllib
import time
import uuid
import collections
import sys
import logging
import json
import colorlog
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer

from simple_fba import (
    handler,
    account,
    node,
)
from simple_fba.storage import Storage


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
log_handler = colorlog.StreamHandler()
log_handler.setFormatter(
    colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        reset=True,
        log_colors={
            # 'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
    ),
)

logging.root.handlers = [log_handler]

log = logging.getLogger(__name__)


class PingSiblings(threading.Thread):
    def __init__(self, server):
        super(PingSiblings, self).__init__()

        self.server = server

    def run_forever(self):
        while True:
            for n in self.server.siblings:
                # log.debug('> start to ping sibling, "%s"', n)
                data = dict(
                    name=self.server.name,
                    port=self.server.server_port,
                )
                response = requests.post(
                    urllib.parse.urljoin(n.endpoint, '/ping'),
                    data=json.dumps(data),
                )
                if response.status_code not in (200,):
                    return False

                s = json.loads(response.text)
                self.name = s['name']
                self.endpoint = s['endpoint']

                # log.debug('< finished to ping sibling: %s', n)

            log.debug('current siblings: %s', repr(self.server.siblings))
            time.sleep(10)

        return

    def run(self):
        time.sleep(1)
        for n in self.server.siblings:
            data = dict(
                name=self.server.name,
                port=self.server.server_port,
            )
            response = requests.post(
                urllib.parse.urljoin(n.endpoint, '/ping'),
                data=json.dumps(data),
            )
            if response.status_code not in (200,):
                return False

            s = json.loads(response.text)
            new_n = node.Node(s['name'], s['endpoint'])
            self.server.siblings.replace(n, new_n)

            log.debug('< finished to ping sibling: %s', n)

        log.debug('current siblings: %s', repr(self.server.siblings))

        return


class BoschainHTTPServer(HTTPServer):
    name = None
    storage = None
    siblings = None
    ballot = None

    def __init__(self, name, storage, siblings, *a, **kw):
        super(BoschainHTTPServer, self).__init__(*a, **kw)

        self.name = name
        self.storage = storage
        self.siblings = siblings
        self.ballot = node.Ballot()

        # TODO this will periodically check whether the node is alive or not
        # t = PingSiblings(self)
        # t.start()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(self.name, self.storage, self.siblings, self.ballot, request, client_address, self)

        return


class BoschainHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    name = None
    storage = None
    siblings = None
    ballot = None

    def __init__(self, name, storage, siblings, ballot, *a, **kw):
        self.name = name
        self.storage = storage
        self.siblings = siblings
        self.ballot = ballot

        super(BoschainHTTPServer_RequestHandler, self).__init__(*a, **kw)

    def do_GET(self):
        log.debug('> start request: %s', self.path)
        parsed = urlparse(self.path)
        func = handler.HTTP_HANDLERS.get(parsed.path[1:].split('/')[0], handler.not_found_handler)
        r = func(self, parsed)

        log.debug('< finished request: %s', self.path)
        return r

    do_POST = do_GET

    def response(self, status_code, message, **headers):
        self.send_response(status_code)
        for k, v in headers.items():
            self.send_header(k, v)

        self.end_headers()

        if message is not None:
            self.wfile.write(bytes(message + ('\n' if message[-1] != '\n' else ''), "utf8"))

        return

    def json_response(self, status_code, message, **headers):
        if type(message) not in (str,):
            message = json.dumps(message)

        headers['Content-Type'] = 'application/json'

        return self.response(status_code, message, **headers)


if __name__ == '__main__':
    options = collections.namedtuple(
        'Options',
        ('init', 'genesis_secret_seed', 'name', 'port', 'siblings'),
    )(False, None, uuid.uuid1().hex, 8001, node.Siblings())

    for i in sys.argv[1:]:
        if i == '-init':
            options = options._replace(init=True)
            continue

        if i.startswith('-genesis='):
            options = options._replace(genesis_secret_seed=i[len('-genesis='):])

        if i.startswith('-name='):
            options = options._replace(name=i[len('-name='):])

        if i.startswith('-port='):
            options = options._replace(port=int(i[len('-port='):]))

        if i.startswith('-siblings='):
            sl = i[len('-siblings='):]
            siblings = node.Siblings()
            for i in filter(lambda x: len(x.strip()) > 0, sl.split(',')):
                siblings.add(node.Node(None, i))

            options = options._replace(siblings=siblings)

    logging.root.setLevel(logging.DEBUG)
    log.debug('options: %s', options)

    node_name = 'node-%s' % options.name
    log.debug('starting node: %s', options.name)

    log.debug('load storage')

    storage = Storage('%s.pkl' % options.name)
    if options.init:
        storage.initialize()
    else:
        storage.load()

    if options.init:
        account.create_genesis(storage, options.genesis_secret_seed)

    node_address = ('0.0.0.0', options.port)
    httpd = BoschainHTTPServer(
        options.name,
        storage,
        options.siblings,  # NOTE siblings is the validators in the same quorum
        node_address,
        BoschainHTTPServer_RequestHandler,
    )

    httpd.serve_forever()
