import sys
import json
import logging
import urllib
import requests
import uuid
from pprint import pprint
from stellar_base.keypair import Keypair

from simple_fba import transaction


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)


def make_transaction(previous_id, source_secret_seed, receiver_address, amount):
    previous_id = uuid.uuid1().hex

    tx = transaction.Transaction(
        previous_id=previous_id,
        receiver_address=receiver_address,
        amount=amount,
        source_secret_seed=source_secret_seed,
    )

    return tx


if __name__ == '__main__':
    log.setLevel(logging.DEBUG)

    node = sys.argv[1]
    source_secret_seed = sys.argv[2]
    receiver_address = sys.argv[3]
    amount = int(sys.argv[4])

    source_kp = Keypair.from_seed(source_secret_seed)
    log.debug('source kp was loaded')

    # get previous_id
    response = requests.get(urllib.parse.urljoin(node, '/transactions/%s?limit=1' % source_kp.address().decode()))
    if response.status_code not in (200,):
        log.error('failed to get transaction history: %s', response.text)
        sys.exit(1)

    histories = json.loads(response.text)
    log.debug('got previous histories: %d', len(histories))
    if len(histories) < 1:
        log.error('no previous transaction history found')
        sys.exit(1)

    previous_id = histories[0]['id']
    tx = make_transaction(
        previous_id,
        source_secret_seed,
        receiver_address,
        amount,
    )

    response = requests.post(
        urllib.parse.urljoin(node, '/transaction'),
        data=tx.sign(),
    )

    if response.status_code not in (200,):
        log.error('failed to send transaction: %s', response.text)
        sys.exit(1)

    print('successfully sent transaction')
    message = tx.to_dict()
    message['body'] = json.loads(message['body'])
    pprint(message)

    sys.exit(0)
