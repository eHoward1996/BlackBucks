import datetime
import os
from multiprocessing import Process

import requests
import yaml
from Crypto.PublicKey import ECC

from src.blockchain import BlockChain
from src.wallet import Wallet


class Node(object):

    blockchain = None
    wallet = None
    other_nodes = set()
    network_yaml = 'config/network.yaml'
    network_config = None

    def __init__(self, ip_address, public, private):
        if public is None or private is None:
            print("Public or Private Key is not defined. Generating new key pair...")

            private = ECC.generate(curve='secp256r1')

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

        self.address = ip_address
        self.public_key = public
        self.private_key = private

        self.network_config = yaml.load(open(self.network_yaml, 'rt'))

        self.broadcast_nodes([ip_address])
        self.other_nodes.add(ip_address)
        self.blockchain = BlockChain()

        self.mining_process = Process(target=self.mine)
        self.mining_process.start()

        self.node_process = Process(
            target=self.app.run,
            args=(ip_address, self.FULL_NODE_PORT)
        )
        self.node_process.start()

        self.wallet = Wallet(
            self.public_key,
            self.private_key,
            self.network_config
        )

    def get_ip_address(self):
        return self.address

    def get_nodes(self):
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

    def register_nodes(self, addresses):
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
            "host": self.host
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
            self.remove_node(node)

        bad_nodes.clear()
        return statuses

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
            self.remove_node(node)

        bad_nodes.clear()
        return "Transaction posted"
        # TODO: convert to grequests and return list of responses

    def mine(self):
        while True:
            last_block = self.blockchain.last_block
            nonce, hashProvided = self.blockchain.proof_of_work(last_block.block_header.nonce)

            # Forge the new block by adding it to the chain
            previous_hash = self.blockchain.hash(last_block)
            block = self.blockchain.new_block(nonce, previous_hash, self.public_address)

            response = {
                'message': "New Block forged",
                'index': block.index,
                'transactions': block.transactions_toListOfDict(),
                'previous_hash': block.block_header.previous_hash,
                'timestamp': block.timestamp,
                'merkle_root': block.block_header.merkle_root,
                'nonce': block.block_header.nonce
            }
            self.broadcast_block(block)
