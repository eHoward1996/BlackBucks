from uuid import uuid4

from Crypto.PublicKey import ECC
from flask import Flask, jsonify, redirect, render_template, request

from BlockChain import BlockChain
from Wallet import Wallet

app = Flask(__name__)

# Generate a globally unique address for the node
node_identifier = str(uuid4()).replace('-', '')
bc = BlockChain()
wallet = None


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        values = request.form

        # Check that the required fields are in the POST data
        required = ['public', 'private']
        for k in required:
            if values[k] is '':
                return render_template('index.html', err="Missing Values")
        else:
            try:
                f = open(values['private'], 'rt')
                privateKey = ECC.import_key(f.read())
                f.close()

                f = open(values['public'], 'rt')
                publicKey = ECC.import_key(f.read())
                f.close()

                if publicKey.export_key(format='PEM') != privateKey.public_key().export_key(format='PEM'):
                    raise Exception('')
            except:
                return render_template('index.html', err="UH OH. IDK, something happened m8")

            # if public != private.public_key.export_key(format="PEM"):
            #     return render_template('index.html', err="Something went wrong")

            global wallet
            wallet = Wallet(publicKey, privateKey)

            return redirect('/main')
    elif request.method == 'GET':
        return render_template('index.html')


@app.route('/main')
def mainPage():
    transactions = None

    return render_template('main.html', transaction_history=transactions)


@app.route('/creation')
def createNewKeys():
    private = ECC.generate(curve='secp256r1')

    f = open('YourPrivateKey.pem', 'wt')
    f.write(private.export_key(format='PEM'))
    f.close()

    f = open('YourPublicKey.pem', 'wt')
    f.write(private.public_key().export_key(format='PEM'))
    f.close()

    return render_template('creation.html', )


@app.route('/transactions', methods=['GET', 'POST'])
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
    return render_template('new.html', summary=jsonify(response, 201))


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
