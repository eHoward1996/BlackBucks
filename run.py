import yaml
from Crypto.PublicKey import ECC

from src.node import Node

user_config = None
public_key = None
private_key = None
ip_address = None
node = None


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
