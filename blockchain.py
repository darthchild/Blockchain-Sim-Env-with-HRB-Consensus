# blockchain.py

import importlib
import threading
from block import Block
import os
import time
from consensus import Consensus
from config import P, G, AUTHORIZED_NODES
import logging
import random
import traceback

class Blockchain:
    def __init__(self, consensus_algorithm, node_id, data_dir):
        self.id = node_id
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.reputation_tokens = self.initialize_reputation_tokens()
        self.chain = [self.create_genesis_block()]
        self.peer_nodes = self.get_peer_nodes(node_id)
        self.authorized_nodes = AUTHORIZED_NODES if consensus_algorithm.lower() == 'poa' else []
        self.consensus = self.load_consensus(consensus_algorithm)
        self.pending_transactions = []  # Initialize empty list for pending transactions
        self.user_db = {}
        self.issued_tokens = {}
        self.p = P
        self.g = G

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
        blockchain_instance = self
        logging.debug(f"[Blockchain] Loading consensus algorithm: {algorithm}")
        try:
            module = importlib.import_module(algorithm)  # Import using lowercase
            consensus_class = getattr(module, algorithm, None)     # Get class directly
            if consensus_class is None:
                raise ImportError(f"Consensus class '{algorithm}' not found")
            return consensus_class(blockchain_instance)          # Pass blockchain instance
        except ImportError as e:
            logging.error(f"Failed to load consensus algorithm: {e}")
            raise e
        except Exception as e:
            logging.error(f"Unexpected error loading consensus: {e}")
            raise e

    def get_last_block(self):
        last_block = self.chain[-1]
        logging.debug(f"[Blockchain] Last block retrieved: {last_block}")
        return last_block

    def add_block(self, user_id, transaction, commitment):
        last_block = self.get_last_block()
        if self.pending_transactions: # Check and add pending transactions 
            transaction = self.pending_transactions
            self.pending_transactions = []

        new_block = self.consensus.initiate_consensus(self, user_id, last_block, transaction, commitment)

        if new_block:  # Consensus successful
            self.consensus.process_new_block(self, new_block)  # Use consensus method, NOT blockchain.chain.append()
            logging.info(f"[Blockchain] Block added by {user_id}")
            return new_block, self.consensus.last_consensus_id  
        else:
            logging.warning("[Blockchain] Consensus failed or block creation failed.")
            return None, None # Return None, None to signal failure


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
        """Initialize reputation tokens dynamically based on peer nodes with random initial values."""
        reputation = {}
        
        # Assign initial reputation to self with a random value
        reputation[self.id] = random.randint(50, 100)  # Example: self-reputation between 50 and 100

        # Define the path to the peers file
        peers_file = os.path.join(self.data_dir, 'peers.txt')

        # Check if peers file exists
        if os.path.exists(peers_file):
            with open(peers_file, 'r') as f:
                peers = f.read().splitlines()

            # Filter out the current node and format peers as node_<port_number>
            peers = [f"node_{peer.split(':')[-1]}" for peer in peers if peer != f"127.0.0.1:{self.id.split('_')[-1]}"]

            # Assign random initial reputation to each peer node
            for node in peers:
                reputation[node] = random.randint(50, 100)  # Assign random reputation values between 50 and 100

            logging.debug(f"[Blockchain] Initialized reputation_tokens with random values: {reputation}")
        else:
            logging.warning(f"[Blockchain] 'peers.txt' not found. Defaulting to a small set of peers.")
            # Default peer nodes (can be adjusted)
            default_peers = [f"node_{i}" for i in range(2, 5)]  # Simulate peer IDs for default peers
            for node in default_peers:
                reputation[node] = random.randint(50, 100)

        return reputation
