import unittest
import uuid

from stellar_base.keypair import Keypair

from .transaction import Transaction


class TestTransaction(unittest.TestCase):
    def test_basic(self):
        previous_id = uuid.uuid1().hex
        receiver_kp = Keypair.random()
        amount = 10
        source_kp = Keypair.random()

        tx = Transaction(
            previous_id=previous_id,
            receiver_address=receiver_kp.address().decode(),
            amount=amount,
            source_secret_seed=source_kp.seed().decode(),
        )
        self.assertEqual(tx.previous_id, previous_id)
        self.assertNotEqual(tx.id, None)
        self.assertEqual(tx.receiver_address, receiver_kp.address().decode())
        self.assertEqual(tx.source_kp.seed(), source_kp.seed())
        self.assertEqual(tx.source_address, source_kp.address().decode())

    def test_signing(self):
        previous_id = uuid.uuid1().hex
        receiver_kp = Keypair.random()
        amount = 10
        source_kp = Keypair.random()

        tx = Transaction(
            previous_id=previous_id,
            receiver_address=receiver_kp.address().decode(),
            amount=amount,
            source_secret_seed=source_kp.seed().decode(),
        )
        signed_message = tx.sign()

        self.assertTrue(type(signed_message) in (dict,))
        self.assertTrue('signature' in signed_message)
        self.assertTrue('body' in signed_message)

    def test_from_message(self):
        previous_id = uuid.uuid1().hex
        receiver_kp = Keypair.random()
        amount = 10
        source_kp = Keypair.random()

        tx = Transaction(
            previous_id=previous_id,
            receiver_address=receiver_kp.address().decode(),
            amount=amount,
            source_secret_seed=source_kp.seed().decode(),
        )
        signed_message = tx.message

        self.assertTrue(type(signed_message) in (str,))

        generated_tx = Transaction.from_message(signed_message)
        self.assertTrue(isinstance(generated_tx, Transaction))

    def test_valiate(self):
        previous_id = uuid.uuid1().hex
        receiver_kp = Keypair.random()
        amount = 10
        source_kp = Keypair.random()

        tx = Transaction(
            previous_id=previous_id,
            receiver_address=receiver_kp.address().decode(),
            amount=amount,
            source_secret_seed=source_kp.seed().decode(),
        )
        signed_message = tx.message

        self.assertTrue(type(signed_message) in (str,))

        self.assertNotEqual(Transaction.validate(signed_message), None)
