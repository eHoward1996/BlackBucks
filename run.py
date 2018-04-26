# import requests
import yaml
from Crypto.PublicKey import ECC
from flask import Flask, jsonify, render_template, request

# import config
from src.node import Node

user_config = None
public_key = None
private_key = None
ip_address = None
node = None

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/main')
def mainPage():
    transactions = None

    if transactions is None:
        transactions = 'No transaction history'
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


# @app.route('/mine', methods=['GET'])
# def mine():
#     last_block = bc.last_block
#     nonce, hashProvided = bc.proof_of_work(last_block.block_header.nonce)

#     # Forge the new block by adding it to the chain
#     previous_hash = bc.hash(last_block)
#     block = bc.new_block(nonce, previous_hash, node_identifier)

#     if type(block) == str:
#         return jsonify({"message": block}), 200

#     response = {
#         'message': "New Block forged",
#         'index': block.index,
#         'transactions': block.transactions_toListOfDict(),
#         'previous_hash': block.block_header.previous_hash,
#         'timestamp': block.timestamp,
#         'merkle_root': block.block_header.merkle_root,
#         'nonce': block.block_header.nonce
#     }

#     return render_template('transactions.html', summary=jsonify(response, 200))


# @app.route('/transactions/new', methods=['POST'])
# def new_transaction():
#     if request.method == 'POST':
#         values = request.form
#     # Check that the required fields are in the POST'ed data
#     required = ['sender', 'recipient', 'amount']
#     if not all(k in values for k in required):
#         return 'Missing Values', 400

#     # Create a new Transaction
#     index = bc.new_transaction(
#         values['sender'],
#         values['recipient'],
#         values['amount']
#     )

#     response = {
#         'message': f'Transaction will be added to block {index}'
#     }
#     return render_template('new.html', summary=jsonify(response, 201))


@app.route('/chain', methods=['GET'])
def full_chain():
    response = node.bc.jsonify()
    return jsonify(response), 200


@app.route('/nodes/copy', methods=['POST'])
def copy_nodes():
    broadcast = request.form.getlist('node_addresses')
    node.recieve_new_nodes(broadcast)
    return jsonify(list(node.other_nodes)), 200


@app.route('/nodes/register', methods=['GET', 'POST'])
def register_nodes():
    if request.method == 'POST':
        nodes = request.form.getlist('node_addr')

        if nodes is None:
            return "Error: Please supply a valid list of nodes\n", 400

        bad_nodes = node.register_nodes(nodes)
        response = {
            'message': 'SUCCESS. All nodes added.',
            'other_nodes': list(node.other_nodes),
        }
        if len(bad_nodes) > 0:
            message = "Bad nodes encountered. Not connecting to network."
            response = {
                'message': message,
                'bad_nodes': list(bad_nodes),
                'nodes_added': list(set(nodes) - set(bad_nodes))
            }

        return jsonify(response), 201
    elif request.method == 'GET':
        return render_template('register.html')


@app.route('/nodes/list', methods=['GET'])
def get_nodes():
    nodes = {
        "other_nodes": list(node.other_nodes)
    }
    return jsonify(nodes), 200


# @app.route('/nodes/resolve', methods=['GET'])
# def consensus():
#     replaced = bc.resolve_conflicts()

#     if replaced:
#         response = {
#             'message': 'Our chain was replaced',
#             'new_chain': bc.jsonify()['blocks']
#         }
#     else:
#         response = {
#             'message': 'Our chain is authoritative',
#             'chain': bc.jsonify()['blocks']
#         }

#     return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "addr",
        type=str,
        help='IP Address for the node'
    )
    args = parser.parse_args()
    addr = args.addr

    try:
        user_config = yaml.load(open('config/user.yaml', 'rt'))
        user_config['host'] = addr

        publicFile = user_config['public_key_file']
        privateFile = user_config['private_key_file']

        if publicFile is not None and privateFile is not None:
            public_key = ECC.import_key(open(f'{publicFile}', 'rt').read())
            private_key = ECC.import_key(open(f'{publicFile}', 'rt').read())

            if public_key.export_key(format='PEM') != private_key.public_key().export_key(format='PEM'):
                raise Exception('Public/Private Key Mismatch')

        node = Node(addr, public_key, private_key)

    except Exception as e:
        print(e)
        exit()

    app.run(
        host=addr
    )
