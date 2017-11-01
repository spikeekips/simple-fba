import json
import logging
import urllib
import requests

from . import transaction


log = logging.getLogger(__name__)


class Node:
    name = None
    endpoint = None

    @classmethod
    def from_json(cls, s):
        d = json.loads(s)

        return cls(**d)

    def __init__(self, name, endpoint):
        self.name = name
        self.endpoint = endpoint

    def to_json(self):
        return json.dumps(dict(
            name=self.name,
            endpoint=self.endpoint,
        ))

    def __repr__(self):
        return '<Node: %s(%s)>' % (self.name, self.endpoint)

    def __eq__(self, a):
        a_endpoint = a.endpoint
        if '//localhost:' in a_endpoint:
            a_endpoint.replace('//localhost:', '//127.0.0.1:')

        b_endpoint = self.endpoint
        if '//localhost:' in b_endpoint:
            b_endpoint.replace('//localhost:', '//127.0.0.1:')

        if a_endpoint == b_endpoint:
            return True

        return False

    def check_ballot_is_opened(self):
        return False

    def broadcast_siblings(self, siblings):
        assert isinstance(siblings, Siblings)

        try:
            response = requests.post(
                urllib.parse.urljoin(self.endpoint, '/ballot'),
                data=Siblings.to_json(),
                timeout=10,
            )
            if response.status_code not in (200,):
                return False
        except Exception as e:
            log.debug('failed to `broadcast_ballot`: %s', e)
            return False

        return True

    def broadcast_ballot(self, ballot):
        assert isinstance(ballot, Ballot)

        try:
            response = requests.post(
                urllib.parse.urljoin(self.endpoint, '/ballot'),
                data=ballot.to_json(),
                timeout=10,
            )
            if response.status_code not in (200,):
                return False
        except Exception as e:
            log.debug('failed to `broadcast_ballot`: %s', e)
            return False

        return True

    def broadcast_agreement_result(self, name, tx_id, result):
        assert result in ('agree', 'disagree')

        data = dict(
            result=result,
            node=name,
        )
        try:
            response = requests.post(
                urllib.parse.urljoin(self.endpoint, '/transaction_agreement/%s' % tx_id),
                data=json.dumps(data),
                timeout=10,
            )
            if response.status_code not in (200,):
                return False
        except:
            return False

        return True

    def ping(self):
        response = requests.post(
            urllib.parse.urljoin(self.endpoint, '/ping'),
            data=self.to_json(),
            timeout=10,
        )
        if response.status_code not in (200,):
            return False

        s = json.loads(response.text)
        self.name = s['name']
        self.endpoint = s['endpoint']

        return True


class Siblings:
    siblings = None

    def __init__(self, *siblings):
        if len(siblings) > 0:
            assert False not in filter(lambda x: isinstance(x, Node), siblings)

        self.siblings = list(siblings)

    def __repr__(self):
        return '<Siblings: %s>' % list(map(lambda x: str(x), self.siblings))

    def __len__(self):
        return len(self.siblings)

    def __iter__(self):
        return self.siblings.__iter__()

    def add(self, node):
        assert isinstance(node, Node)

        for i, n in enumerate(self.siblings[:]):
            if n == node:
                del self.siblings[i]
                break

        self.siblings.append(node)

        return True

    def replace(self, a, b):
        for i, n in enumerate(self.siblings[:]):
            if n.endpoint == a.endpoint:
                del self.siblings[i]
                break

        self.add(b)

        return

    def remove(self, name):
        for i, n in enumerate(self.siblings[:]):
            if n.name == name:
                del self.siblings[i]

        return


class Ballot:
    transaction = None

    result = None

    def __init__(self):
        self.transaction = None

        self.result = dict(
            agree=list(),
            disagree=list(),
            failed=list(),
        )

    def to_json(self):
        return self.transaction.to_json()

    def __repr__(self):
        return '<Ballot: %s: agree=%s disagree=%s failed=%s>' % (
            self.transaction.id,
            self.result['agree'],
            self.result['disagree'],
            self.result['failed'],
        )

    @property
    def is_closed(self):
        return self.transaction is None

    def close(self):
        self.transaction = None

        self.result = dict(
            agree=list(),
            disagree=list(),
            failed=list(),
        )

        return

    def open(self, transaction):
        self.transaction = transaction

        self.result = dict(
            agree=list(),
            disagree=list(),
            failed=list(),
        )

        return

    def open_from_json(self, s):
        assert self.is_closed

        self.open(transaction.Transaction.from_message(s))

        return

    def set_result(self, k, v):
        assert not self.is_closed and k in self.result
        self.result[k].append(v)

        return

    @property
    def agree(self):
        return self.result['agree']

    @property
    def disagree(self):
        return self.result['disagree']

    @property
    def failed(self):
        return self.result['failed']
