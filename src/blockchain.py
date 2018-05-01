import requests
from Crypto.Hash import SHA256

from src.block import Block
from src.transaction import Transaction


class BlockChain(object):
    """
        Python implementation of BlockChain
    """

    # List of nodes in the cryptocurrency network
    nodes = set()

    maxTransactions = 4
    blocks = []

    def __init__(self, blocks=None):
        # List of currently unpublished transactions
        self.unpublished_transactions = []

        # Create genisis block
        if blocks is None:
            genesis_block = self.generate_genesis_block()
            self.add_block(genesis_block)
        else:
            for block in blocks():
                self.add_block(block)

    def generate_genesis_block(self):
        genesis_transactions = []
        t1 = Transaction(
            "0",
            "6d9c84400e035877ee464e070b5d8bf01880ca2fb060062a71b43cdb58497c39",
            25,
            "",
        )
        t2 = Transaction(
            "0",
            "6d9c84400e035877ee464e070b5d8bf01880ca2fb060062a71b43cdb58497c39",
            25,
            "",
        )
        genesis_transactions.append(t1)
        genesis_transactions.append(t2)

        for i in range(2):
            genesis_transactions.append(Transaction(
                "0",
                "-",
                0,
                "",
            ))

        genesis_block = Block(0, genesis_transactions, "", 1)
        return genesis_block

    def add_block(self, block):
        self.blocks.append(block)

    def new_block(self, nonce, previous_hash, block_owner):
        # Creates new block and adds it to the chain
        """
            Create a new block in the block chain

            :param proof: <int> The proof given by the Proof of Work algorithm
            :param previous_hash: (Optional) <str> Hash of previous Block
            :param block_owner: (Optional) <str> If this is not None, a block was mined
            :return: <Block> New Block
        """

        if len(self.unpublished_transactions) < 1:
            return "There are no unpublished transactions. No new block will be created and/or added."

        added_transactions = []
        for i in range(self.maxTransactions):
            if i < len(self.unpublished_transactions):
                added_transactions.append(self.unpublished_transactions.pop(0))
            else:
                break

        # We must recieve a reword for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin.
        added_transactions.append(Transaction(
            "0",
            block_owner,
            self.get_reward(),
            ""
        ))

        b = Block(
            index=self.size(),
            transactions=added_transactions,
            previous_hash=previous_hash,  # or self.hash(self.blocks[-1]),
            nonce=nonce
        )

        self.blocks.append(b)
        return b

    def new_transaction(self, transaction):
        # Adds a new transaction to the list of transactions
        """
            Creates a new transaction to go into the next mined Block

            :param senderAddr: <str> Address of the Sender
            :param recipientAddr: <str> Address of the Recipient
            :param amountSent: <float> Amount
            :param signed: <str> Signature verifying transaction
            :return: <int> index of the Block that will hold the transaction
        """

        self.unpublished_transactions.append(transaction)
        return True

    def get_balance(self, address):
        balance = 0
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.origin == address:
                    balance -= transaction.amount
                if transaction.destination == address:
                    balance += transaction.amount

        return balance

    def get_transaction_history(self, address):
        tx = []
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.origin == address or transaction.destination == address:
                    t = transaction.jsonify()
                    t['time'] = transaction.timestamp
                    t['block_number'] = block.index
                    tx.append(t)

        return tx

    def get_reward(self):
        return 25

    def size(self):
        return len(self.blocks)

    @staticmethod
    def hash(block):
        # Hashes a Block
        """
            Creates a SHA256 hash of a block

            :param block: <Block> Block
            :return: <str>
        """

        block_string = block.stringify()
        return SHA256.new(str.encode(block_string)).hexdigest()

    @property
    def last_block(self):
        # Returns the last block in the chain
        try:
            return self.blocks[-1]
        except IndexError:
            return None

    def proof_of_work(self, last_proof):
        """
            Simple Proof of Work Algorithm:
                - Find a numbder p' such that hash(pp') contains 4 leading zeroes,
                    where p is the previous p'
                - p is the previous proof, and p' is the new proof

                :param last_proof: <int>
                :return: <int>
        """
        nonce = 0
        satisfied, guess = self.valid_proof(last_proof, nonce)

        while satisfied is False:
            nonce += 1
            satisfied, guess = self.valid_proof(last_proof, nonce)

        return nonce, guess

    @staticmethod
    def valid_proof(last_proof, nonce):
        """
            Validates the Proof: Does Hash(last_proof, nonce) contains 4 leading zeroes?

            :param last_proof: <int> Previous Proof
            :param proof: <int> Current number of guesses
            :return: <bool> True if Correct, False is not
        """

        guess = f'{last_proof}{nonce}'.encode()
        guess_hash = SHA256.new(guess).hexdigest()

        return guess_hash[:4] == "0000", guess_hash

    def valid_chain(self, chain):
        """
            Determine if a given blockchain is valid

            :param chain: <list> a Blockchain
            :return: <bool> True is valid, False if not
        """

        last_block = chain[0]
        current_index = 1
        if_valid_blocks = []

        while current_index < len(chain):
            block = chain[current_index]

            # Check that the hash of the block is correct
            trans = []
            for t in last_block['transactions']:
                trans.append(Transaction(
                    origin=t['origin'],
                    destination=t['destination'],
                    amount=t['amount'],
                    signature=t['signature']
                ))

            last_block = Block(
                last_block['index'],
                trans,
                last_block['previous_hash'],
                last_block['nonce']
            )

            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block.block_header.previous_hash, last_block.block_header.nonce):
                return False

            last_block = block
            current_index += 1
            if_valid_blocks.append(last_block)

        return True, if_valid_blocks

    def resolve_conflicts(self):
        """
            This is our Consensus Algorithm, it resolves conflicts
            by replacing our chain with the longest one in the network.

            :return: <bool> True if our chain was replaced, False if not
        """

        neighbors = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.blocks)

        # Grab and verify the chains from all the nodes in out network
        for node in neighbors:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['blocks']

                # Check if the length is longer and the chain valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            blocks = []
            for i in range(len(new_chain)):
                trans = []
                for t in new_chain[i]['transactions']:
                    trans.append(Transaction(
                        origin=t['origin'],
                        destination=t['destination'],
                        amount=t['amount'],
                        signature=t['signature']
                    ))

                blocks.append(Block(
                    i,
                    trans,
                    new_chain[i]['previous_hash'],
                    new_chain[i]['nonce']
                ))

            self.blocks = blocks
            return True

        return False

    def jsonify(self):
        r = {}
        blx = []
        for b in self.blocks:
            blx.append(b.jsonify())

        r['blocks'] = blx
        r['length'] = len(blx)
        return r
