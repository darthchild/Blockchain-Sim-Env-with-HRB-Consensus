# PoWConsensus.py

import hashlib
import json
import threading
from config import DIFFICULTY_LEVEL
import time
from datetime import datetime
import random
from consensus import Consensus
from block import Block
from node_communication import broadcast_block, broadcast_node_selection_complete
import logging
import traceback

class PoWConsensus(Consensus):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()
        self.DIFFICULTY = DIFFICULTY_LEVEL
        self.reward = 10
        self.found_time = -1
        self.node_select_result = (None, None)  # Initialize node_select_result as a tuple (new_block, node_id)
        logging.debug(f"[PoWConsensus] Initialized with DIFFICULTY: {self.DIFFICULTY} and reward: {self.reward}")
    
    def node_select(self, user_id, last_block, transaction, commitment, block_data, blockchain):
        node_id = blockchain.id  # e.g., 'node_5000'
        nonce = random.randint(0, 10000000)
        logging.info(f"[node_select] Initial nonce selected: {nonce} for {node_id}")
        self.DIFFICULTY = DIFFICULTY_LEVEL  # Ensure difficulty is set to the required level
        self.found_time = -1  # Reset found_time
        self.stop_event.clear()  # Ensure the event is cleared before starting

        while not self.stop_event.is_set():
            block_data['nonce'] = nonce
            block_data['timestamp'] = time.time()
            block_hash = self.calculate_hash(block_data)
            if block_hash.startswith('0' * self.DIFFICULTY):
                self.found_time = time.time()
                logging.info(f"[node_select] Block mined with hash: {block_hash}")
                broadcast_node_selection_complete(blockchain.peer_nodes, node_id, self.found_time)
                break
            nonce += 1

        if not self.stop_event.is_set():
            new_block = Block(user_id, last_block.hash, transaction, commitment, timestamp=block_data['timestamp'], nonce=nonce)
            self.node_select_result = (new_block, node_id)  # Store the result here
            return new_block, node_id
        else:
            logging.info("[node_select] Mining stopped before a valid block was found.")
            self.node_select_result = (None, None)  # Clear the result if stopped
            return None, None
        
    def stop_selection(self, stop_time):
        """Stop the mining process if another node found a block earlier."""
        if self.found_time == -1 or self.found_time > stop_time:
            logging.info("[stop_selection] Stopping mining as another node found a block earlier.")
            self.stop_event.set()
        else:
            logging.info("[stop_selection] Not stopping mining; this node found the block first.")
    
    def calculate_hash(self, block_data):
        """Calculate the SHA-256 hash of the block data."""
        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def validate_block(self, blockchain, new_block, consensus_id):
        """Validate the mined block."""
        last_block = blockchain.get_last_block()
        
        logging.debug("[validate_block] New block data:")
        logging.debug(new_block)
        logging.debug("[validate_block] Last block data:")
        logging.debug(last_block)
    
        if new_block is None:
            logging.error("[validate_block] No block provided for validation!")
            return False
            
        if new_block.hash.startswith('0' * self.DIFFICULTY) and new_block.previous_hash == last_block.hash:
            blockchain.reputation_tokens[consensus_id] += self.reward
            logging.info(f"[validate_block] Block validated. Reputation tokens for {consensus_id} increased by {self.reward}.")
            return True
            
        logging.warning("[validate_block] Block validation failed.")
        return False
    
    def process_new_block(self, blockchain, new_block):
        """Add the block to the blockchain."""
        blockchain.chain.append(new_block)
        logging.info(f"[process_new_block] Block added by {new_block.user_id} to the blockchain.")
        logging.debug(f"[process_new_block] Updated reputation tokens: {blockchain.reputation_tokens}")
    
        blockchain.update_metrics(new_block)
