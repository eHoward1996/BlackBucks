import json
from time import time

from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS


class Transaction():

	def __init__(self, origin, destination, amount, signature=None):
		self._origin = origin
		self._destination = destination
		self._amount = amount
		self._timestamp = int(time())
		self._signature = signature
		self._transaction_hash = None

		if self._signature is not None:
			self._transaction_hash = self._calculateTransactionHash()

	@property
	def origin(self):
		return self._origin

	@property
	def destination(self):
		return self._destination

	@property
	def amount(self):
		return self._amount

	@property
	def timestamp(self):
		return self._timestamp

	@property
	def transaction_hash(self):
		return self._transaction_hash

	@property
	def signature(self):
		return self._signature

	def _calculateTransactionHash(self):
		"""
			Calculates sha256 hash of transaction
			(origin, destination, amount, timestamp, signature)

			:return: sha256 hash
			:rtype: str
		"""
		data = {
			"source": self.origin,
			"destination": self.destination,
			"amount": self.amount,
			"timestamp": self.timestamp,
			"signature": self.signature
		}
		data_json = json.dumps(data, sort_keys=True)
		hash_object = SHA256.new(str.encode(data_json))

		return hash_object.hexdigest()

	def sign(self, private_key):
		signer = DSS.new(private_key, 'fips-186-3')
		signature = signer.sign(self.stringify())

		self._signature = signature
		self._transaction_hash = self._calculateTransactionHash()
		return signature

	def stringify(self):
		return ":".join((
			self._origin,
			self._destination,
			str(self._amount),
			str(self.signature)
		))

	def verify_sender(self):
		key = ECC.import_key(self._source)
		verifier = DSS.new(key, 'fips-186-3')
		verifier.verify(self.stringify(), self._signature)

	def jsonify(self):
		data = {
			"origin": self.origin,
			"destination": self.destination,
			"amount": str(self.amount),
			"signature": self.signature,
			"tx_hash": self.transaction_hash
		}

		return data
