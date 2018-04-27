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
    node.recieve_new_transaction(request.form['transactions'])
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
            'nodes_added': list(node.other_nodes),
            'bad_nodes': []
        }
        if len(bad_nodes) > 0:
            message = "Bad nodes encountered. Not connecting to network."
            response = {
                'message': message,
                'bad_nodes': list(bad_nodes),
                'nodes_added': list(set(nodes) - set(bad_nodes))
            }

        good = "Good Nodes: ", response['nodes_added']
        bad = "Bad Nodes: ", response['bad_nodes']

        return render_template(
            'peers.html',
            message=response['message'],
            good_nodes=good,
            bad_nodes=bad,
            peers=node.get_nodes()
        )
    elif request.method == 'GET':
        return render_template(
            'peers.html',
            peers=node.get_nodes()
        )


@app.route('/nodes/list', methods=['GET'])
def get_nodes():
    nodes = {
        "other_nodes": list(node.other_nodes)
    }
    return jsonify(nodes), 200


@app.route('/blocks', methods=['POST'])
def post_block():
    new_block = node.recieve_new_block(request.form['block'])
    return jsonify(new_block), 200


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
            private_key = ECC.import_key(open(f'{privateFile}', 'rt').read())

            if public_key.export_key(format='PEM') != private_key.public_key().export_key(format='PEM'):
                raise Exception('Public/Private Key Mismatch')

            if not private_key.has_private():
                raise Exception('Private key cannot be used for signing')

        node = Node(addr, public_key, private_key)

    except Exception as e:
        print(e)
        exit()

    app.run(
        host=addr
    )
