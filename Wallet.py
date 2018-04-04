import random

from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

import requests
from Transaction import Transaction


class Wallet():
    __private_key__ = None
    __public_key__ = None

    def __init__(self, private_key=None):
        if private_key is not None:
            self.__private_key__ = ECC.import_key(private_key)
        else:
            print("No private key provided. Generating new key pair")
            self.__private_key__ = ECC.generate(curve='secp256r1')

        self.__public_key__ = self.__private_key__.public_key()

    def get_public_key(self):
        return self.__public_key__.export_key(format='PEM')

    def get_private_key(self):
        return self.__private_key__.export_key(format='PEM')

    def sign(self, message):
        hashMessage = SHA256.new(message)
        signer = DSS.new(self.get_private_key(), 'fips-186-3')
        signature = signer.sign(hashMessage)

        return signature

    def verify(self, signature, message, public_key=None):
        if public_key is None:
            public_key = self.get_public_key()

        verifier = DSS.new(public_key, 'fips-186-3')
        return verifier.verify(message, signature)

    def get_balance(self, address=None, node=None):
        if address is None:
            address = self.get_public_key()
        if node is None:
            node = random

        url = self.BALANCE_URL.format(node, self.FULL_NODE_PORT, address)

        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestsException as re:
            pass
        return None

    def get_transaction_history(self, address=None, node=None):
        if address is None:
            address = self.get_public_key()
        if node is None:
            node = random.sample(self.full_nodes, 1)[0]
        url = self.TRANSACTION_HISTORY_URL.format(node, self.FULL_NODE_PORT, address)
        try:
            response = requests.get(url)
            return response.json()
        except requests.exceptions.RequestsException as re:
            pass
        return None

    def create_transaction(self, to, amount):
        transaction = Transaction(
            self.get_public_key(),
            to,
            amount
        )
        transaction.sign(self.get_private_key())
        return self.broadcast_transaction(transaction)


if __name__ == "__main__":
    pass
