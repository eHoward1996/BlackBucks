import datetime
import os
from multiprocessing import Process

import requests
import yaml
from Crypto.PublicKey import ECC
from flask import Flask, jsonify, render_template, request

from src.blockchain import BlockChain
from src.wallet import Wallet


class Node(object):

    other_nodes = set()
    network_yaml = 'config/network.yaml'
    network_config = None
    app = Flask(__name__)

    def __init__(self, ip_address, public, private):
        if public is None or private is None:
            print("Public or Private Key is not defined. Generating new key pair...")

            private = ECC.generate(curve='secp256r1')
            self.private_key = private
            self.public_key = private.public_key()

            f = open('YourPrivateKey.pem', 'wt')
            f.write(private.export_key(format='PEM'))
            f.close()

            f = open('YourPublicKey.pem', 'wt')
            f.write(private.public_key().export_key(format='PEM'))
            f.close()

            print(
                "New keys generated at ",
                os.getcwd(),
                "\n",
                "Using newly generated keys for node creation."
            )
        else:
            self.public_key = public
            self.private_key = private

        self.address = ip_address
        self.network_config = yaml.load(open(self.network_yaml, 'rt'))

        self.broadcast_nodes([ip_address])
        self.other_nodes.add(ip_address)
        self.blockchain = BlockChain()

        self.wallet = Wallet(
            self.public_key,
            self.private_key,
            self.network_config
        )

        self.mining_process = Process(target=self.mine)
        self.mining_process.start()

        self.node_process = Process(target=self.app.run, args=self.get_ip_address())
        self.node_process.start()             

    def get_ip_address(self):
        return self.address

    def get_other_nodes(self):
        return self.other_nodes

    def request_nodes(self, node, port):
        url = self.network_config['nodes_url'].format(node, port)
        try:
            response = requests.get(url)
            if response is not None:
                return node
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_all_nodes(self):
        bad_nodes = set()

        for node in self.other_nodes:
            if node != self.address:
                node_addr = self.request_nodes(node, self.network_config['node_port'])
                if node_addr is None:
                    bad_nodes.add(node)

        for node in bad_nodes:
            self.other_nodes.discard(node)

    def register_new_nodes(self, addresses):
        addresses_to_add = set(addresses) - self.other_nodes
        non_active_nodes = set()

        for node in addresses_to_add:
            url = self.network_config['nodes_url'].format(node, self.network_config['node_port'])
            try:
                requests.get(url)
            except requests.exceptions.RequestException as re:
                non_active_nodes.add(node)

        addresses_to_add -= non_active_nodes
        self.broadcast_nodes(list(addresses_to_add))
        self.other_nodes ^= addresses_to_add
        self.introduce_other_nodes(list(addresses_to_add))
        return non_active_nodes

    def broadcast_nodes(self, addresses):
        self.request_all_nodes()

        bad_nodes = set()
        data = {
            "node_addr": addresses
        }

        for node in self.other_nodes:
            if node == self.address:
                continue

            url = self.network_config['register_url'].format(node, self.network_config['node_port'])
            try:
                requests.post(url, data=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.other_nodes.discard(node)

    def introduce_other_nodes(self, addresses):
        known_addresses = list(self.other_nodes)

        data = {
            "node_addresses": known_addresses
        }

        for address in addresses:
            url = self.network_config['copy_nodes_url'].format(address, self.network_config['node_port'])
            try:
                requests.post(url, data=data)
            except requests.exceptions.RequestException as re:
                print("SHEESH! THAT'S NO BUENO!")

    def recieve_new_nodes(self, addresses):
        for addr in addresses:
            if addr not in self.other_nodes:
                self.other_nodes.add(addr)

    def recieve_new_transaction(self, transaction):
        self.blockchain.new_transaction(transaction)

    def recieve_new_block(self, block):
        self.blockchain.add_block(block)

    def get_balance(self):
        return self.blockchain.get_balance(self.wallet.get_public_address())

    def get_transaction_history(self):
        tx = self.blockchain.get_transaction_history(self.wallet.get_public_address())
        for t in tx:
            stamp = t['time']
            t['time'] = datetime.datetime.fromtimestamp(stamp).strftime('%b %d %Y %H %M %S')

        return tx

    def broadcast_block(self, block):
        self.request_all_nodes()
        bad_nodes = set()

        data = {
            "block": block,
            "host": self.address
        }

        for node in self.other_nodes:
            if node == self.address:
                continue

            url = "http://{}:{}/blocks".format(node, 5000)
            try:
                requests.post(url, data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)

        for node in bad_nodes:
            self.other_nodes.discard(node)

        bad_nodes.clear()
        # return statuses

    def broadcast_transaction(self, recipient, amount):
        if int(amount) > self.get_balance():
            return "Not enough BlackBucks for transaction!"

        self.request_all_nodes()
        bad_nodes = set()

        tx = self.wallet.create_transaction(recipient, amount)
        self.blockchain.new_transaction(tx)

        data = {
            "transaction": tx.jsonify()
        }

        for node in self.other_nodes:
            if node != self.address:
                url = self.network_config['add_tx_url'].format(node, self.network_config['node_port'])
                try:
                    requests.post(url, data=data)
                except requests.exceptions.RequestException as re:
                    bad_nodes.add(node)

        for node in bad_nodes:
            self.other_nodes.discard(node)

        bad_nodes.clear()
        return "Transaction posted"
        # TODO: convert to grequests and return list of responses

    def mine(self):
        while True:
            last_block = self.blockchain.last_block

            if last_block is not None:
                nonce, _ = self.blockchain.proof_of_work(last_block.block_header.nonce)

                # Forge the new block by adding it to the chain
                previous_hash = self.blockchain.hash(last_block)
                block = self.blockchain.new_block(nonce, previous_hash, self.address)
                if type(block) is not str:                    
                    response = {
                        'message': "New Block forged",
                        'index': block.index,
                        'transactions': block.transactions_toListOfDict(),
                        'previous_hash': block.block_header.previous_hash,
                        'timestamp': block.timestamp,
                        'merkle_root': block.block_header.merkle_root,
                        'nonce': block.block_header.nonce
                    }
                    print(response)
                    self.broadcast_block(block)


    @app.route('/', methods=['GET'])
    def index(self):
        return render_template(
            'index.html',
            public_address=self.wallet.get_public_address(),
            balance=self.get_balance(),
            transactions=self.get_transaction_history()
        )


    @app.route('/transactions', methods=['GET', 'POST'])
    def create_transaction(self):
        if request.method == 'GET':
            return render_template(
                'transactions.html',
                public_address=self.wallet.get_public_address(),
                #public_address=node.wallet.get_public_address(),
                balance=self.get_balance()
            )
        elif request.method == 'POST':
            values = request.form

            # Check that the required fields are in the POST'ed data
            required = ['recipient', 'amount']
            if not all(k in values for k in required):
                return render_template(
                    'transactions.html',
                    public_address=self.wallet.get_public_address(),
                    balance=self.get_balance(),
                    response="Missing Values"
                )

            # Create a new Transaction
            response = self.broadcast_transaction(
                values['recipient'],
                values['amount']
            )

            return render_template(
                'transactions.html',
                public_address=self.wallet.get_public_address(),
                balance=self.get_balance(),
                response=response
            )


    @app.route('/blockchain', methods=['GET'])
    def chain(self):
        response = self.blockchain.jsonify()
        return render_template('blockchain.html', chain=response)


    @app.route('/nodes/copy', methods=['POST'])
    def copy_nodes(self):
        broadcast = request.form.getlist('node_addresses')
        self.recieve_new_nodes(broadcast)
        return jsonify(list(self.other_nodes)), 200


    @app.route('/transactions/copy', methods=['POST'])
    def copy_transactions(self):
        self.recieve_new_transaction(request.form['transactions'])
        return jsonify(list(self.other_nodes)), 200


    @app.route('/nodes/register', methods=['GET', 'POST'])
    def register_nodes(self):
        if request.method == 'POST':
            nodes = request.form.getlist('node_addr')

            if nodes is None:
                return "Error: Please supply a valid list of nodes\n", 400

            bad_nodes = self.register_new_nodes(nodes)
            response = {
                'message': 'SUCCESS. All nodes added.',
                'nodes_added': list(self.other_nodes),
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
                peers=self.get_other_nodes()
            )
        elif request.method == 'GET':
            return render_template(
                'peers.html',
                peers=self.get_other_nodes()
            )


    @app.route('/nodes/list', methods=['GET'])
    def get_nodes(self):
        nodes = {
            "other_nodes": list(self.other_nodes)
        }
        return jsonify(nodes), 200


    @app.route('/blocks', methods=['POST'])
    def post_block(self):
        new_block = self.recieve_new_block(request.form['block'])
        return jsonify(new_block), 200
