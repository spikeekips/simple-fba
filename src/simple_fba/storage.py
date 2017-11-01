import pathlib
import logging
import pickle


log = logging.getLogger(__name__)


class Storage:
    data = None

    def __init__(self, name):
        self.name = name
        self.data = dict()

    def initialize(self):
        self.data = dict()
        self.save()

        return

    def load(self):
        if not pathlib.Path(self.name).exists():
            log.debug('storage, "%s" was newly created', self.name)
            self.save()

            return

        with open(self.name, 'rb') as f:
            self.data = pickle.load(f)

        return

    def get(self, k, *a, **kw):
        return self.data.get(k, *a, **kw)

    def set(self, k, v):
        self.data[k] = v
        self.save()

        return

    def save(self):
        with open(self.name, 'wb') as f:
            pickle.dump(self.data, f)

        return

    def get_account(self, address):
        return self.get('account.%s' % address)

    def set_account(self, address, v):
        return self.set('account.%s' % address, v)

    def get_transaction(self, id):
        return self.get('transaction.%s' % id)

    def set_transaction(self, id, v):
        self.set('transaction.%s' % id, v)

        txs = self.get_transactions(v['source_address'])
        if txs is None:
            txs = list()

        txs.insert(0, v)
        self.set('transactions.%s' % v['source_address'], txs)

        return

    def get_transactions(self, address):
        txs = self.get('transactions.%s' % address)
        if txs is None:
            txs = list()

        return txs

    def add_transaction_to_pool(self, tx):
        if 'pool' not in self.data:
            self.data['pool'] = list()

        self.data['pool'].insert(0, tx)
        self.save()

        return
