import coincurve
import hashlib
import json

from time import time


class Transaction():

	def __init__(self, origin, destination, amount, signature=None):
		self._origin = origin
		self._destination = destination
		self._amount = amount
		self._timestamp = time()
		self._signature = signature

		if self._signature is not None:
			self.tx_hash = self.calculateTXHash()

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
	def tx_hash(self):
		return self._tx_hash

	@property
	def signature(self):
		return self._signature

	def _calculate_tx_hash(self):
		"""
			Calculates sha256 hash of transaction
			(source, destination, amount, timestamp, signature)

			:return: sha256 hash
			:rtype: str
		"""
		data = {
			"source": self.source,
			"destination": self.destination,
			"amount": self.amount,
			"timestamp": self.timestamp,
			"signature": self.signature
		}
		data_json = json.dumps(data, sort_keys=True)
		hash_object = hashlib.sha256(data_json)

		return hash_object.hexdigest()
