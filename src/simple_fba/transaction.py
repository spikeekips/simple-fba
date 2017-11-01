import uuid
import json
# import datetime
import logging
import base64

from stellar_base.keypair import Keypair
from stellar_base.utils import DecodeError as stellar_base_DecodeError


log = logging.getLogger(__name__)


class Transaction:
    id = None
    previous_id = None
    source_address = None
    receiver_address = None
    amount = None
    signature = None

    # NOTE `created_time` is just for history
    # created_time = None

    # TODO One `Transaction` can store the multiple `operation`s, at this time for simplicity one `Transaction` have one `operation`.
    # operations = None
    # signatures = None

    source_kp = None

    def __init__(self, previous_id, receiver_address, amount, id=None, source_secret_seed=None, source_address=None, signature=None):
        assert type(amount) in (int,)

        if id is not None:
            self.id = id
        else:
            self.id = uuid.uuid1().hex

        self.previous_id = previous_id
        self.receiver_address = receiver_address
        self.amount = amount
        # self.created_time = None  # `created_time` will be set when submitting
        self.signature = signature

        if source_address is not None:
            self.source_address = source_address

        self.source_kp = None
        if source_secret_seed is not None:
            self.source_kp = Keypair.from_seed(source_secret_seed)
            self.source_address = self.source_kp.address().decode()

        assert self.source_address is not None

    @classmethod
    def validate(cls, message):
        try:
            return cls._validate(message)
        except KeyError as e:
            import traceback
            traceback.print_exc()
            log.debug('failed to check message: %s', e)
            return None

    @classmethod
    def _validate(cls, message):
        '''
        `transaction_message` is just for simple json string. `validate()` will return the `Transaction` instance.
        '''

        j = json.loads(message)

        body = json.loads(j['body'])

        # verification of address
        try:
            Keypair.from_address(body['source_address'])
        except stellar_base_DecodeError as e:
            log.debug('failed to check `source_address`: %s', e)
            return None

        try:
            Keypair.from_address(body['receiver_address'])
        except stellar_base_DecodeError as e:
            log.debug('failed to check `receiver_address`: %s', e)
            return None

        # verification of signature and body
        try:
            Keypair.from_address(body['source_address']).verify(j['body'].encode('utf-8'), base64.b64decode(j['signature']))
        except Exception as e:
            import traceback
            traceback.print_exc()
            log.debug('failed to check signature from message, "%s": %s', message, e)
            return None

        if body['amount'] < 0:
            log.debug('failed to check amount: invalid `amount`, %d', body['amount'])
            return None

        return cls.from_message(message)

    @classmethod
    def from_message(cls, message):
        '''
        this `message` must be validated
        '''

        # TODO exception handling will be added
        j = json.loads(message)
        body = json.loads(j['body'])
        tx = cls(
            body['previous_id'],
            body['receiver_address'],
            body['amount'],
            id=body['id'],
            source_secret_seed=None,
            source_address=body['source_address'],
        )
        tx.id = j['id']
        tx.source_address = j['source_address']
        tx.signature = j['signature']
        # if 'created_time' in j:
        #     tx.created_time = j['created_time']

        return tx

    @property
    def body(self):
        # if self.created_time is None:
        #     self.created_time = datetime.datetime.now().isoformat()

        return dict(
            id=self.id,
            previous_id=self.previous_id,
            source_address=self.source_address,
            receiver_address=self.receiver_address,
            amount=self.amount,
            # created_time=self.created_time,
        )

    def to_dict(self):
        return dict(
            id=self.id,
            source_address=self.body['source_address'],
            signature=self.signature,
            body=json.dumps(self.body),
        )

    def to_json(self):
        return json.dumps(self.to_dict())

    __str__ = to_json

    def sign(self):
        '''
        `sign` will return the signed dict message
        '''
        if self.source_kp is None:
            raise

        body = json.dumps(self.body)
        signature = self.source_kp.sign(body.encode('utf-8'))
        self.signature = base64.b64encode(signature).decode('utf-8')

        return self.to_json()
