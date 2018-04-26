import os
import select
import socket
import threading
from time import time

import requests
import yaml
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC

from src.blockchain import BlockChain
from src.wallet import Wallet


class Node(object):

    wallet = None
    client = None
    server = None

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
        self.public_key = private.public_key()
        self.public_address = SHA256.new(str.encode(self.public_key.export_key(format='PEM'))).hexdigest()
        self.private_key = private

        self.network_config = yaml.load(open(self.network_yaml, 'rt'))

        self.broadcast_nodes([ip_address])
        self.other_nodes.add(ip_address)
        self.bc = BlockChain()

        # self.mining_process = Process(target=self.mine)
        # self.mining_process.start()

        # self.node_process = Process(
        #     target=self.app.run,
        #     args=(ip_address, self.FULL_NODE_PORT)
        # )
        # self.node_process.start()

        self.wallet = Wallet(public, private)

    def get_public_address(self):
        return self.public_address

    def get_ip_address(self):
        return self.address

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
        nodes = self.other_nodes.copy()
        bad_nodes = set()

        for node in nodes:
            if node != self.address:
                node_addr = self.request_nodes(node, self.network_config['node_port'])
                if node_addr is not None:
                    nodes = nodes.add(node_addr)
                else:
                    bad_nodes.add(node)

        self.other_nodes = nodes

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

    def broadcast_block(self, block):
        # TODO convert to grequests and concurrently gather a list of responses
        statuses = {
            "confirmations": 0,
            "invalidations": 0,
            "expirations": 0
        }

        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "block": block,
            "host": self.host
        }

        for node in self.full_nodes:
            url = "http://{}:{}/blocks".format(node, 5000)
            try:
                response = requests.post(url, data)
                if response.status_code == 202:
                    # confirmed and accepted by node
                    statuses["confirmations"] += 1
                elif response.status_code == 406:
                    # invalidated and rejected by node
                    statuses["invalidations"] += 1
                elif response.status_code == 409:
                    # expired and rejected by node
                    statuses["expirations"] += 1
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return statuses

    def broadcast_transaction(self, transaction):
        self.request_nodes_from_all()
        bad_nodes = set()
        data = {
            "transaction": transaction.to_json()
        }

        for node in self.full_nodes:
            url = self.TRANSACTIONS_URL.format(node, self.FULL_NODE_PORT)
            try:
                response = requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)
        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return
        # TODO: convert to grequests and return list of responses
