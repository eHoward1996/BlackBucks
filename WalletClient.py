import random

import coincurve
import requests

import Transaction


class WalletClient():

	__priv_key = None
	__pub_key = None

	def __init__(self, private_key=None):
		if private_key is not None:
			self.__priv_key = coincurve.PrivateKey.from_hex(private_key)
		else:
			print("No private key provided. Generating new key pair")
			self.__priv_key = coincurve.PrivateKey

		self.pub_key = self.__priv_key.public_key

	def get_public_key(self):
		return self.pub_key.format(compressed=True).encode('hex')

	def get_private_key(self):
		return self.__priv_key.to_hex()

	def sign(self, message):
		return self.__priv_key.sign(message).encode('hex')

	def verify(self, signature, message, public_key=None):
		if public_key is not None:
			return coincurve.PublicKey(public_key).verify(signature, message)

		return self.pub_key.verify(signature, message)

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
			amount,
			self.get_private_key
		)
		return self.broadcast_transaction(transaction)


if __name__ == "__main__":
	pass
