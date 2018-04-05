from urllib.parse import urlparse
import requests
from Crypto.Hash import SHA256

from Block import Block
from Transaction import Transaction


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
        for i in range(4):
            genesis_transactions.append(Transaction(
                "0",
                "0",
                0,
                "",
            ))

        genesis_block = Block(0, genesis_transactions, "", 100)
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

    def new_transaction(self, senderAddr, recipientAddr, amountSent, signed=None):
        # Adds a new transaction to the list of transactions
        """
            Creates a new transaction to go into the next mined Block

            :param senderAddr: <str> Address of the Sender
            :param recipientAddr: <str> Address of the Recipient
            :param amountSent: <float> Amount
            :param signed: <str> Signature verifying transaction
            :return: <int> index of the Block that will hold the transaction
        """

        self.unpublished_transactions.append(Transaction(
            senderAddr,
            recipientAddr,
            amountSent,
            signed
        ))

        return self.size()

    def get_balance(self, address):
        balance = 0
        for block in self.blocks:
            for transaction in block.transactions:
                if transaction.origin == address:
                    balance -= transaction.amount
                if transaction.destination == address:
                    balance += transaction.amount

        return balance

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
        return self.blocks[-1]

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

    def register_node(self, address):
        """
            Add a new node to the list of nodes

            :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
            :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        for x in address:
            self.resolve_conflicts()

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
<<<<<<< Updated upstream


# Instantiate the Node
app = Flask(__name__)

# Generate a globally unique address for the node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
bc = BlockChain()

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/transactions')
def start_transaction():
    return render_template('transactions.html')

@app.route('/mine', methods=['GET'])
def mine():
    last_block = bc.last_block
    nonce, hashProvided = bc.proof_of_work(last_block.block_header.nonce)

    # Forge the new block by adding it to the chain
    previous_hash = bc.hash(last_block)
    block = bc.new_block(nonce, previous_hash, node_identifier)

    if type(block) == str:
        return jsonify({"message": block}), 200

    response = {
        'message': "New Block forged",
        'index': block.index,
        'transactions': block.transactions_toListOfDict(),
        'previous_hash': block.block_header.previous_hash,
        'timestamp': block.timestamp,
        'merkle_root': block.block_header.merkle_root,
        'nonce': block.block_header.nonce
    }

    return render_template('transactions.html', summary=jsonify(response, 200))


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    #values = request.get_json()
    #response = requests.post(url, json={"user": user, "pass": password})
    if request.method == 'POST':
        values = request.form
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    # Create a new Transaction
    index = bc.new_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    response = {
        'message': f'Transaction will be added to block {index}'
    }
    return render_template('transactions.html', summary=jsonify(response, 201))


@app.route('/chain', methods=['GET'])
def full_chain():
    response = bc.jsonify()
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes\n", 400

    for node in nodes:
        bc.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(bc.nodes),
    }

    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = bc.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': bc.jsonify()['blocks']
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': bc.jsonify()['blocks']
        }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        '-p',
        '--port',
        default=5000,
        type=int,
        help='port to listen on'
    )
    args = parser.parse_args()
    port = args.port

    app.run(
        host='127.0.0.1',
        port=port
    )
=======
>>>>>>> Stashed changes
