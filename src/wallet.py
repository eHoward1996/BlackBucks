import random

import requests
from Crypto.Hash import SHA256
from Crypto.Signature import DSS

from src.transaction import Transaction


class Wallet():
    __private_key__ = None
    __public_key__ = None
    __public_address__ = None

    def __init__(self, public_key, private_key, network_config):
        self.__public_key__ = public_key
        self.__private_key__ = private_key
        self.__public_address__ = SHA256.new(str.encode(self.__public_key__.export_key(format='PEM'))).hexdigest()

        self.network_config = network_config

    def get_public_address(self):
        return self.__public_address__

    def get_public_key(self):
        return self.__public_key__.export_key(format='PEM')

    def get_private_key(self):
        return self.__private_key__.export_key(format='PEM')

    def sign(self, message):
        hashMessage = SHA256.new(str.encode(message))
        signer = DSS.new(self.__private_key__, 'fips-186-3')
        signature = signer.sign(hashMessage)

        return signature

    def verify(self, signature, message, public_key=None):
        if public_key is None:
            public_key = self.get_public_key()

        verifier = DSS.new(public_key, 'fips-186-3')
        return verifier.verify(message, signature)

    def create_transaction(self, to, amount):
        m = [
            self.__public_address__,
            to,
            amount
        ]
        m = ":".join(m)
        signature = self.sign(m)

        tx = Transaction(
            self.get_public_address(),
            to,
            amount,
            signature
        )
        tx.sign(self.get_private_key())
        return tx


if __name__ == "__main__":
    pass
