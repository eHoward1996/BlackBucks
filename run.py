import yaml
from Crypto.PublicKey import ECC
from flask import Flask, jsonify, render_template, request

from src.node import Node

user_config = None
public_key = None
private_key = None
ip_address = None
node = None

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template(
        'index.html',
        public_address=node.wallet.get_public_address(),
        balance=node.get_balance(),
        transactions=node.get_transaction_history()
    )


@app.route('/transactions', methods=['GET', 'POST'])
def create_transaction():
    if request.method == 'GET':
        return render_template(
            'transactions.html',
            public_address=node.wallet.get_public_address(),
            balance=node.get_balance()
        )
    elif request.method == 'POST':
        values = request.form

        # Check that the required fields are in the POST'ed data
        required = ['recipient', 'amount']
        if not all(k in values for k in required):
            return render_template(
                'transactions.html',
                public_address=node.wallet.get_public_address(),
                balance=node.get_balance(),
                response="Missing Values"
            )

        # Create a new Transaction
        response = node.broadcast_transaction(
            values['recipient'],
            values['amount']
        )

        return render_template(
            'transactions.html',
            public_address=node.wallet.get_public_address(),
            balance=node.get_balance(),
            response=response
        )


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


@app.route('/blockchain', methods=['GET'])
def chain():
    response = node.blockchain.jsonify()
    return render_template('blockchain.html', chain=response)


@app.route('/nodes/copy', methods=['POST'])
def copy_nodes():
    broadcast = request.form.getlist('node_addresses')
    node.recieve_new_nodes(broadcast)
    return jsonify(list(node.other_nodes)), 200


@app.route('/transactions/copy', methods=['POST'])
def copy_transactions():
    broadcast = request.form['transaction']
    node.recieve_new_transaction(broadcast)
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
