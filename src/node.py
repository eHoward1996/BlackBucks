from BlockChain import BlockChain


class Node(object):

    full_nodes = set()

    def __init__(self, host, reward_address):
        self.host = host
        self.request_nodes_from_all()
        self.reward_address = reward_address
        self.broadcast_node(host)
        self.full_nodes.add(host)

        self.bc = BlockChain()

        mining = kwargs.get("mining")
        if mining is True:
            self.NODE_TYPE = "miner"
            self.mining_process = Process(target=self.mine)
            self.mining_process.start()
            logger.debug(
                "mining node started on %s with reward address of %s...", host, reward_address)
        logger.debug(
            "full node server starting on %s with reward address of %s...", host, reward_address)
        self.node_process = Process(
            target=self.app.run, args=(host, self.FULL_NODE_PORT))
        self.node_process.start()
        logger.debug(
            "full node server started on %s with reward address of %s...", host, reward_address)

    def request_nodes(self, node, port):
        url = self.NODES_URL.format(node, port)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                all_nodes = response.json()
                return all_nodes
        except requests.exceptions.RequestException as re:
            pass
        return None

    def request_nodes_from_all(self):
        full_nodes = self.full_nodes.copy()
        bad_nodes = set()

        for node in full_nodes:
            all_nodes = self.request_nodes(node, self.FULL_NODE_PORT)
            if all_nodes is not None:
                full_nodes = full_nodes.union(all_nodes["full_nodes"])
            else:
                bad_nodes.add(node)
        self.full_nodes = full_nodes

        for node in bad_nodes:
            self.remove_node(node)
        return

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
