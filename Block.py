import Transaction


class Block():

	blockTransactions = []

	def __init__(self, index_in_chain, unpublished_transactions, previous_hash, timestamp):
		"""
			:param index_in_chain: index # of block
			:type index: int

			:param unpublished_transactions: list of unpublished transactions
			:type unpublished_transactions: list of transaction objects

			:param previous_hash: previous block hash
			:type previous_hash: str

			:param timestamp: timestamp of block mined
			:type timestamp: int
		"""
		self._index = index_in_chain
		self._transactions = unpublished_transactions
		self._previous = previous_hash
		self._timestamp = timestamp
		self.block_header = Header(self._previous, self._timestamp)

	@property
	def index(self):
		return self._index

	@property
	def transactions(self):
		return self._transactions

	@property
	def previous(self):
		return self._previous

	@property
	def timestamp(self):
		return self._timestamp


class Header():

	def __init__(self, previous_hash, merkle_root, timestamp):
		self.previous_hash = previous_hash
		self.merkle_root = merkle_root
		self.timestamp = timestamp
