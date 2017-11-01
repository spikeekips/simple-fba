import logging
from stellar_base.keypair import Keypair

from . import (
    account,
    transaction,
)


log = logging.getLogger(__name__)


class Account:
    address = None
    balance = None

    def __init__(self, address, balance):
        self.address = address
        self.balance = balance

    def to_dict(self):
        return dict(
            address=self.address,
            balance=self.balance,
        )


def create_genesis(storage, secret_seed):
    # create genesis account
    if secret_seed is not None:
        kp = Keypair.from_seed(secret_seed)
    else:
        kp = Keypair.random()

    genesis = dict(
        secret_seed=kp.seed().decode(),
        address=kp.address().decode(),
        balance=10 * 10,
    )
    storage.set(
        'genesis',
        genesis['address'],
    )
    storage.set_account(
        genesis['address'],
        account.Account(genesis['address'], genesis['balance']).to_dict(),
    )
    log.debug('geensis account was created: %s', genesis)

    # make transaction for genesis
    tx = transaction.Transaction(
        None,  # genesis transaction does not have `previous_id`
        genesis['address'],
        genesis['balance'],
        source_secret_seed=genesis['secret_seed'],
    )

    signed_message = tx.sign()
    storage.set_transaction(
        tx.id,
        tx.to_dict(),
    )
    log.debug('genesis transaction was occured: %s', signed_message)

    return
