# blockchain.py

import importlib
import threading
from block import Block
import os
import time
from consensus import Consensus
from config import P, G, AUTHORIZED_NODES
import logging
import traceback

class Blockchain:
    def __init__(self, consensus_algorithm, node_id, data_dir):
        self.id = node_id
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.chain = [self.create_genesis_block()]
        self.peer_nodes = self.get_peer_nodes(node_id)
        self.authorized_nodes = AUTHORIZED_NODES if consensus_algorithm.lower() == 'poa' else []
        self.consensus = self.load_consensus(consensus_algorithm)
        self.user_db = {}
        self.issued_tokens = {}
        self.p = P
        self.g = G
        self.reputation_tokens = self.initialize_reputation_tokens()

        self.metrics = {
            'block_times': [],               # List to store time taken for each block
            'transactions_per_block': [],    # List to store number of transactions per block
            'block_sizes': [],               # List to store size of each block in bytes
            'total_size': 0,                 # Cumulative size of the blockchain
            'difficulty': []                 # List to store difficulty levels
        }
        self.last_block_time = self.chain[0].timestamp  # Initialize with genesis block timestamp

        logging.debug(f"[Blockchain] Initialized with node_id: {self.id}, data_dir: {self.data_dir}")
        logging.debug(f"[Blockchain] Peer nodes: {self.peer_nodes}")
        logging.debug(f"[Blockchain] Consensus algorithm: {consensus_algorithm}")

    def create_genesis_block(self):
        logging.info("[Blockchain] Creating genesis block.")
        genesis_block = Block("genesis", "0", "Genesis Block", "genesis_commitment", timestamp=1, nonce="nonce")
        logging.debug(f"[Blockchain] Genesis block created: {genesis_block}")
        return genesis_block

    def load_consensus(self, algorithm):
        logging.debug(f"[Blockchain] Loading consensus algorithm: {algorithm}")
        class_name = algorithm

        try:
            module = importlib.import_module(f"{algorithm}")
            consensus_class = getattr(module, class_name, None)
            if consensus_class is None:
                logging.error(f"Consensus class '{class_name}' not found in {algorithm}_consensus")
                raise ImportError(f"Consensus class '{class_name}' not found in {algorithm}_consensus")
            logging.info(f"[Blockchain] Consensus algorithm '{class_name}' loaded successfully.")
            return consensus_class()
        except ImportError as e:
            logging.error(f"[Blockchain] Failed to load consensus algorithm: {e}")
            raise e
        except Exception as e:
            logging.error(f"[Blockchain] Unexpected error while loading consensus algorithm: {e}")
            raise e

    def get_last_block(self):
        last_block = self.chain[-1]
        logging.debug(f"[Blockchain] Last block retrieved: {last_block}")
        return last_block

    def add_block(self, user_id, transaction, commitment):
        last_block = self.get_last_block()
        block_data = {
            'user_id': user_id,
            'previous_hash': last_block.hash,
            'transaction': transaction,
            'commitment': commitment
        }

        try:
            # Start mining in a separate thread
            mining_thread = threading.Thread(target=self.consensus.node_select, args=(user_id, last_block, transaction, commitment, block_data, self))
            mining_thread.start()
            mining_thread.join()  # Wait for mining to finish

            new_block, consensus_id = self.consensus.node_select_result
            if new_block is not None:
                logging.info(f"[Blockchain] New block created by '{consensus_id}': {new_block}")
                if self.consensus.validate_block(self, new_block, consensus_id):
                    self.consensus.process_new_block(self, new_block)
                    logging.info("[Blockchain] Block added to the local chain.")
                    return new_block, consensus_id
                else:
                    logging.error("[Blockchain] Block validation failed.")
                    return None, None
            else:
                logging.warning("[Blockchain] Current node did not mine a block.")
                return None, None
        except Exception as e:
            logging.error(f"[Blockchain] Exception occurred while adding block: {e}")
            logging.debug(traceback.format_exc())
            return None, None


    def update_metrics(self, new_block):
        logging.debug(f"[Blockchain] Updating metrics with new block: {new_block}")
        block_time = new_block.timestamp - self.last_block_time
        self.metrics['block_times'].append(block_time)
        self.last_block_time = new_block.timestamp  # Update for the next block
        logging.debug(f"[Blockchain] Block time: {block_time} seconds.")

        self.metrics['transactions_per_block'].append(1)  # Modify if multiple transactions per block
        logging.debug(f"[Blockchain] Transactions per block updated: {self.metrics['transactions_per_block']}")

        block_size = new_block.size_in_bytes()
        self.metrics['block_sizes'].append(block_size)
        logging.debug(f"[Blockchain] Block size: {block_size} bytes.")

        self.metrics['total_size'] += block_size
        logging.debug(f"[Blockchain] Total blockchain size: {self.metrics['total_size']} bytes.")

        if hasattr(self.consensus, 'DIFFICULTY'):
            current_difficulty = self.consensus.DIFFICULTY
        else:
            current_difficulty = 0  # For PoS or if difficulty not applicable
        self.metrics['difficulty'].append(current_difficulty)
        logging.debug(f"[Blockchain] Current difficulty: {current_difficulty}")

    def get_peer_nodes(self, current_node_id):
        """Retrieve peer nodes based on the current node's ID."""
        logging.debug(f"[Blockchain] Retrieving peer nodes for '{current_node_id}'.")
        # Dynamically discover peers based on data_dir or other configurations
        # For simplicity, assuming all nodes are on localhost with ports ranging from 5000 to 5000 + number_of_nodes
        # Modify this method as per your deployment strategy

        # Example: Read a peer list from a configuration file within data_dir
        peers_file = os.path.join(self.data_dir, 'peers.txt')
        if os.path.exists(peers_file):
            with open(peers_file, 'r') as f:
                peers = f.read().splitlines()
            peers = [peer for peer in peers if peer != f"127.0.0.1:{self.id.split('_')[-1]}"]
            logging.debug(f"[Blockchain] Peer nodes from file: {peers}")
            return peers
        else:
            # Default peer nodes (can be adjusted)
            default_peers = ["127.0.0.1:5001", "127.0.0.1:5002"]  # Add more as needed
            logging.warning(f"[Blockchain] 'peers.txt' not found. Using default peers: {default_peers}")
            return default_peers

    def initialize_reputation_tokens(self):
        """Initialize reputation tokens dynamically based on peer nodes."""
        reputation = {}
        # Assign initial reputation to self
        reputation[self.id] = 10

        # Define the path to the peers file
        peers_file = os.path.join(self.data_dir, 'peers.txt')
        
        # Check if peers file exists
        if os.path.exists(peers_file):
            with open(peers_file, 'r') as f:
                peers = f.read().splitlines()

            # Filter out the current node and format peers as node_<port_number>
            peers = [f"node_{peer.split(':')[-1]}" for peer in peers if peer != f"127.0.0.1:{self.id.split('_')[-1]}"]

            # Assign initial reputation to each peer node
            for node in peers:
                reputation[node] = 10  # Default reputation value for each peer node

            logging.debug(f"[Blockchain] Initialized reputation_tokens: {reputation}")
        else:
            logging.debug(f"File does not exist: {peers_file}")
        
        return reputation

