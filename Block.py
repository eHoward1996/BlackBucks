from time import time

from collections import OrderedDict

from Crypto.Hash import SHA256
from Transaction import Transaction


class Block():
    blockTransactions = []

    def __init__(self, index, transactions, previous_hash, nonce):
        """
            :param index: index # of block
            :type index: int

            :param transactions: list of unpublished transactions
            :type transactions: list of transaction objects

            :param previous_hash: previous block hash
            :type previous_hash: str

            :param nonce: the nonce of work for the mined block
            :type nonce: str
        """

        self._index = index
        self._transactions = transactions
        self._timestamp = int(time())
        self.merkleTree = MerkleTree(self._transactions)
        self.block_header = Header(previous_hash, self.merkleTree.get_root(), nonce, self.timestamp)

    @property
    def index(self):
        return self._index

    @property
    def transactions(self):
        return self._transactions

    @property
    def timestamp(self):
        return self._timestamp

    def stringify(self):
        r = ""
        for t in self.transactions:
            r += t.stringify() + ":"

        r += str(self.index) + ":"
        r += str(self.block_header.previous_hash) + ":"
        r += str(self.block_header.nonce)
        return r

    def transactions_toListOfDict(self):
        transactionsForJSON = []
        for t in self.transactions:
            transactionsForJSON.append(t.jsonify())

        return transactionsForJSON

    def jsonify(self):
        data = {
            "index": self.index,
            "transactions": self.transactions_toListOfDict(),
            "previous_hash": self.block_header.previous_hash,
            "nonce": self.block_header.nonce,
            "merkle_root": self.merkleTree.get_root()
        }
        return data


class Header():

    def __init__(self, previous_hash, merkle_root, nonce, timestamp):
        self.previous_hash = previous_hash
        self.merkle_root = merkle_root
        self.timestamp = timestamp
        self.nonce = nonce


class MerkleTree():

    def __init__(self, transactions=None):
        self.list_of_transactions = transactions
        self.past_transaction = OrderedDict()
        self.create_tree()

    def create_tree(self):
        listoftransaction = self.list_of_transactions
        past_transaction = self.past_transaction
        temp_transaction = []

        for index in range(0, len(listoftransaction), 2):
            left_leaf = listoftransaction[index]
            if index + 1 != len(listoftransaction):
                right_leaf = listoftransaction[index + 1]
            else:
                right_leaf = ''

            left_leaf_hash = left_leaf.stringify() if type(left_leaf) == Transaction else left_leaf
            left_hash = SHA256.new(str.encode(left_leaf_hash))

            if right_leaf != '':
                right_leaf_hash = right_leaf.stringify() if type(right_leaf) == Transaction else right_leaf
                right_hash = SHA256.new(str.encode(right_leaf_hash))

            past_transaction[listoftransaction[index]] = left_hash.hexdigest()

            if right_leaf != '':
                past_transaction[listoftransaction[index + 1]] = right_hash.hexdigest()
                temp_transaction.append(left_hash.hexdigest() + right_hash.hexdigest())
            else:
                temp_transaction.append(left_hash.hexdigest())

        if len(listoftransaction) != 1:
            self.list_of_transactions = temp_transaction
            self.past_transaction = past_transaction
            self.create_tree()

    def get_past_transacion(self):
        return self.past_transaction

    def get_root(self):
        # last_key = self.past_transaction.iterkeys()[-1]
        key_list = list(self.past_transaction.items())[-1]
        return self.past_transaction[key_list[0]]
