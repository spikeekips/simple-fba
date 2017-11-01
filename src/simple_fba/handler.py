import math
import urllib
import threading
import json
import logging

from . import (
    node,
    transaction,
)


log = logging.getLogger(__name__)


def not_found_handler(server, parsed):
    if parsed.path[1:] == '':
        return handle_ping(server, parsed)

    # TODO this will be replaced with the http problem protocol,
    # https://tools.ietf.org/html/draft-ietf-appsawg-http-problem-00
    message = '"%s" not found' % parsed.path
    server.response(404, message)

    return


def handle_ping(server, parsed):
    if server.command not in ('POST',):
        server.response(405, None)
        return

    length = int(server.headers['Content-Length'])
    post_data = server.rfile.read(length).decode('utf-8')

    d = json.loads(post_data)
    host, _ = server.request.getpeername()
    endpoint = 'http://%s:%s' % (host, d['port'])

    if server.siblings.add(node.Node(d['name'], endpoint)):
        log.debug('got node, %s, and added', post_data)
    else:
        log.debug('got node, %s, but already exists', post_data)

    host, port = server.request.getsockname()
    info = dict(
        name=server.name,
        endpoint='http://%s:%s' % (host, port),
    )
    server.json_response(200, info)

    return


def handle_transactions(server, parsed):
    if server.command not in ('GET',):
        server.response(405, None)
        return

    qs = urllib.parse.parse_qs(parsed.query)

    paths = parsed.path[1:].split('/')
    if len(paths) < 2:
        server.response(400, None)
        return

    # get latest transaction of the account
    txs = server.storage.get_transactions(paths[1])

    limit = None
    if 'limit' in qs:
        limit = int(qs['limit'][0])

    server.json_response(200, txs[:limit])

    return


def handle_transaction(server, parsed):
    if server.command not in ('GET', 'POST',):
        server.response(405, None)
        return

    if server.command in ('GET',):
        return _handle_transaction_get(server, parsed)

    if server.command in ('POST',):
        return _handle_transaction_post(server, parsed)

    return


def _handle_transaction_get(server, parsed):
    paths = parsed.path[1:].split('/')
    if len(paths) < 2:
        server.response(400, None)
        return

    # get transaction by transaction id
    tx = server.storage.get_transaction(paths[1])

    if tx is None:
        server.response(404, None)
        return

    server.json_response(200, tx)

    return


def _handle_transaction_post(server, parsed):
    length = int(server.headers['Content-Length'])
    post_data = server.rfile.read(length).decode('utf-8')
    log.debug('got transaction: %s', post_data)

    log.info('> trying to validate transaction: %s', post_data)
    validated_tx = transaction.Transaction.validate(post_data)
    if validated_tx is None:
        log.info('< failed to validate, %s', post_data)
        server.json_response(401, 'failed to validate')

        return

    log.info('< [%s] validated', validated_tx.id)

    log.info('> [%s] trying to check ballot is opened', validated_tx.id)
    if not server.ballot.is_closed:  # opened
        log.error('< [%s] the ballot is opened, the transaction will be saved in the pool', validated_tx.id)

        server.storage.add_transaction_to_pool(validated_tx)
        server.json_response(200, None)

        return

    log.info('< [%s] the ballot is closed', validated_tx.id)
    for n in server.siblings:
        log.info('> [%s] trying to check the siblings ballot is opened or not: %s', validated_tx.id, n)
        # TODO if ballot is opened, check the transaction in ballot
        if n.check_ballot_is_opened():
            log.error('< [%s] found opened ballot at %s', validated_tx.id, n)
            continue

        log.info('< [%s] not found opened ballot at %s', validated_tx.id, n)

    log.info('> [%s] start new ballot with new transaction', validated_tx.id)
    server.ballot.open(validated_tx)
    server.ballot.agree.append('self')
    log.info('< [%s] new ballot was created: %s', validated_tx.id, server.ballot)

    log.info('> [%s] trying to broadcast the ballot to siblings', validated_tx.id)
    for n in server.siblings:
        if not n.broadcast_ballot(server.ballot):
            log.info('< [%s] node, "%s" did not accept new ballot', validated_tx.id, n)

    log.info('> [%s] start new agreement', validated_tx.id)

    # server.storage.set_transaction(validated_tx.id, validated_tx.to_dict())

    # log.debug('saved: %s', validated_tx)

    server.json_response(200, None)

    return


class BroadcastAgreementResult(threading.Thread):
    def __init__(self, server, tx_id, result):
        super(BroadcastAgreementResult, self).__init__()

        self.server = server
        self.tx_id = tx_id
        self.result = result

    def run(self):
        host, port = self.server.request.getsockname()
        for n in self.server.siblings:
            n.broadcast_agreement_result('http://%s:%d' % (host, port), self.tx_id, self.result)

        return


def handle_ballot(server, parsed):
    if not server.ballot.is_closed:
        server.json_response(400, None)

        return

    log.info('> received new ballot')
    length = int(server.headers['Content-Length'])
    post_data = server.rfile.read(length).decode('utf-8')

    server.ballot.open_from_json(post_data)

    log.info('> trying to validate ballot')

    d = json.loads(post_data)
    validated_tx = transaction.Transaction.validate(post_data)

    if validated_tx is not None:
        log.info('< [%s] received transaction was validated', validated_tx.id)

    result = 'disagree' if validated_tx is None else 'agree'
    t = BroadcastAgreementResult(server, d['id'], result)
    t.start()

    server.json_response(200, None)

    return


def handle_transaction_agreement(server, parsed):
    if server.command not in ('POST',):
        server.response(405, None)
        return

    paths = parsed.path[1:].split('/')
    if len(paths) < 2:
        server.response(400, None)
        return

    tx_id = paths[1]
    if server.ballot.is_closed:
        log.info('[%s] ballot is already closed', tx_id)

        server.json_response(200, None)

        return

    tx = server.ballot.transaction
    if tx.id != tx_id:
        log.error('[%s] transaction id does not match with the one in the ballot; "%s" != "%s"', tx_id, tx_id, tx.id)
        server.response(400, None)

        return

    length = int(server.headers['Content-Length'])
    data = json.loads(server.rfile.read(length).decode('utf-8'))
    result = data['result']
    if result not in ('agree', 'disagree'):
        log.error('< [%s] got invalid result, "%s"', tx.id, result)

        server.response(400, None)

        return

    log.info('> [%s] got the agreement from %s', tx.id, data['node'])
    server.ballot.set_result(result, data['node'])
    log.info('< [%s] current agreement: %s', tx.id, server.ballot)

    # check threshold: majority vote
    threshold = math.ceil(len(server.siblings) * 0.5)
    agreed = len(server.ballot.agree)
    log.info('check threshold: %d > %d', agreed, threshold)
    if agreed <= threshold:
        server.json_response(200, None)
        return

    # close ballot
    server.ballot.close()

    log.info('satisfied threshold: %d > %d', agreed, threshold)
    server.storage.set_transaction(tx.id, tx.to_dict())

    return


HTTP_HANDLERS = dict(
    ping=handle_ping,
    transaction=handle_transaction,
    transactions=handle_transactions,
    transaction_agreement=handle_transaction_agreement,
    ballot=handle_ballot,
)
