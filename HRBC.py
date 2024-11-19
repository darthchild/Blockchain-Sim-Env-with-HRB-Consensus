# hrbc.py
import hashlib
import json
import threading
import time
import random
from consensus import Consensus
from block import Block
from node_communication import broadcast_block, broadcast_node_selection_complete
import logging
import traceback


class HRBC(Consensus):
    def __init__(self, blockchain):
        super().__init__()
        self.blockchain = blockchain  # Reference to the blockchain object
        self.node_properties = self.initialize_node_properties()
        self.clusters = self.form_clusters()
        self.cluster_leaders = self.elect_cluster_leaders()
        self.super_node = self.elect_super_node()
        self.reward = 10
        self.penalty = 20  # Penalty for misbehavior
        self.decay_rate = 0.01  # Reputation decay rate per block
        self.node_select_result = (None, None)  # For storing the mining results


    def initialize_node_properties(self):
        """Randomly initializes properties for each node."""
        node_properties = {}
        for node_id in self.blockchain.reputation_tokens.keys():
            node_properties[node_id] = {
                'uptime': random.uniform(0.9, 1.0),  # Uptime percentage (90%-100%)
                'network_proximity': random.uniform(0.0, 1.0),  # Proximity (0 is closest)
            }
        logging.debug(f"[HRBC] Node properties initialized: {node_properties}")
        return node_properties


    def initiate_consensus(self, blockchain_instance, user_id, last_block, transactions, commitment):
        node_id = blockchain_instance.id
        cluster_id = self.get_cluster_id(node_id)
        logging.debug(f"[HRBC] initiate_consensus called: node_id={node_id}, cluster_id={cluster_id}, transactions={transactions}")

        if cluster_id is not None and node_id == self.cluster_leaders[cluster_id]:
            proposed_block = self.create_block(user_id, last_block.hash, transactions, commitment)
            logging.debug(f"[HRBC] Proposed block created: {proposed_block}")


            if proposed_block:
                consensus_result = self.perform_inter_cluster_consensus(blockchain_instance, proposed_block)
                logging.debug(f"[HRBC] Inter-cluster consensus result: {consensus_result}, votes = {self.votes}") # Assuming 'self.votes' tracks votes

                if consensus_result:
                    self.last_consensus_id = blockchain_instance.id
                    return proposed_block
                else:
                    logging.warning("[HRBC] Inter-cluster consensus failed.")
                    return None
            else:
                logging.warning("[HRBC] Block creation failed.")
                return None
        else:
            logging.debug(f"[HRBC] Node {node_id} is not the cluster leader.")  # Indicate non-leader behavior
            return None # Return None if consensus is not successful

    def form_clusters(self):
        """Forms clusters based on network proximity."""
        clusters = {}
        num_clusters = 3  # You can adjust the number of clusters
        nodes = list(self.blockchain.reputation_tokens.keys())

        # Sort nodes based on their network proximity
        nodes_sorted_by_proximity = sorted(
            nodes, key=lambda node: self.node_properties[node]['network_proximity']
        )

        # Equally divide nodes into clusters
        cluster_size = len(nodes) // num_clusters
        for i in range(num_clusters):
            start = i * cluster_size
            end = (i + 1) * cluster_size if i < num_clusters - 1 else len(nodes)
            clusters[i] = nodes_sorted_by_proximity[start:end]

        logging.debug(f"[HRBC] Clusters formed based on network proximity: {clusters}")
        return clusters


    def elect_cluster_leaders(self):
        """Elects cluster leaders based on reputation."""
        cluster_leaders = {}
        for cluster_id, nodes in self.clusters.items():
            # Find max based on blockchain.reputation_tokens scores
            leader = max(nodes, key=lambda node: self.blockchain.reputation_tokens.get(node, 0))
            cluster_leaders[cluster_id] = leader

        logging.debug(f"[HRBC] Cluster leaders elected: {cluster_leaders}")

        return cluster_leaders


    def elect_super_node(self):
        """Elects the super node (highest reputation among CLs)."""
        # Max of cluster leaders by reputation_tokens score
        super_node = max(self.cluster_leaders.values(), key=lambda node: self.blockchain.reputation_tokens.get(node, 0))
        logging.debug(f"[HRBC] Super node elected: {super_node}")
        return super_node

    def calculate_hash(self, block_data):
         """Calculate the SHA-256 hash of the block data."""
         block_string = json.dumps(block_data, sort_keys=True).encode()
         return hashlib.sha256(block_string).hexdigest()



    def node_select(self, user_id, last_block, transaction, commitment, block_data, blockchain):
        """Handles node selection and block mining within a cluster."""
        node_id = blockchain.id
        self.stop_event.clear() # Clear any previous stop signals

        # 1. Intra-cluster Consensus
        for cluster_id, nodes in self.clusters.items():
            if node_id in nodes:
                leader_id = self.cluster_leaders[cluster_id]
                if node_id == leader_id:
                    logging.debug(f"[HRBC] Node {node_id} is the cluster leader for cluster {cluster_id}")
                    new_block = self.mine_block(user_id, last_block, transaction, commitment, block_data)

                    if new_block: # Intra-cluster voting successful
                        self.node_select_result = (new_block, node_id)
                        return new_block, node_id
                    else:
                        self.node_select_result = (None, None)
                        return None, None # Mining failed or stopped
                elif not self.stop_event.is_set(): # Participate in voting if not the leader
                    vote = self.vote_on_block(new_block)
                    #... (Handle vote and consensus within the cluster)
                    logging.debug(f"[HRBC] Voting results (Simulation): {vote}") 
                else:
                    logging.debug(f"[HRBC] Mining/voting stopped for node {node_id} in cluster {cluster_id}")
                    self.node_select_result = (None, None)
                    return None, None
        self.node_select_result = (None, None)
        return None, None # Node not in any cluster


    def mine_block(self, user_id, last_block, transaction, commitment, block_data):
        """Mines a new block (Simplified PoW for demonstration)."""
        nonce = 0
        while not self.stop_event.is_set():  # Check for stop signal
            block_data['nonce'] = nonce
            block_data['timestamp'] = time.time()
            block_hash = self.calculate_hash(block_data)
            if block_hash.startswith('0' * 4): # Simple PoW condition
                new_block = Block(user_id, last_block.hash, transaction, commitment, timestamp=block_data['timestamp'], nonce=nonce)
                logging.info(f"[HRBC] Block mined by {self.blockchain.id}: {new_block}")
                broadcast_node_selection_complete(self.blockchain.peer_nodes, self.blockchain.id, time.time()) # Notify others
                return new_block
            nonce += 1
        return None  # Mining stopped



    def vote_on_block(self, block):
        """Simulates voting on a block within a cluster."""
        return random.choice([True, True, True, False]) # Example: 75% chance of a positive vote


    def validate_block(self, blockchain, new_block, consensus_id):
        """Validates the mined block and updates reputations."""
        last_block = blockchain.get_last_block()
        if new_block.previous_hash == last_block.hash and new_block.hash.startswith("0" * 4): # Basic Block Validation (PoW condition)

            # Implement Cluster Leader and Super Node checks here:

            self.update_reputation(blockchain, consensus_id, 1) # Validation Success. 
            return True
        else:
            self.update_reputation(blockchain, consensus_id, -1) # Validation Failure
            return False


    def process_new_block(self, blockchain, new_block):
        blockchain.chain.append(new_block)
        logging.info(f"[HRBC Consensus] Block added to blockchain: {new_block}")
        blockchain.update_metrics(new_block)
        self.decay_reputation(blockchain)


    def update_reputation(self, blockchain, node_id, status):
        if status == 1:
           blockchain.reputation_tokens[node_id] += self.reward # Slow increase, quick to lose
        elif status == -1:
            blockchain.reputation_tokens[node_id] -= self.penalty  # Apply penalty for negative actions

        #Update cluster leaders and super node if reputations changed
        self.cluster_leaders = self.elect_cluster_leaders()
        self.super_node = self.elect_super_node()



    def decay_reputation(self, blockchain):
        for node_id in blockchain.reputation_tokens:
            blockchain.reputation_tokens[node_id] *= (1 - self.decay_rate)  # Decay reputation

    
    def create_block(self, user_id, previous_hash, transactions, commitment): # Modified to accept transaction list
        """Creates a new block."""
        block_data = {
            'user_id': user_id,
            'previous_hash': previous_hash,
            'transaction': transactions, # List of transactions
            'commitment': commitment,
            'timestamp': time.time(),
            'nonce': 0  # You might need to remove nonce or handle it differently if not using PoW.
        }
        new_block = Block(user_id, previous_hash, transactions, commitment, timestamp=block_data['timestamp'], nonce=0) # Corrected the instantiation
        return new_block
    
    def get_cluster_id(self, node_id):
        for cluster_id, nodes in self.clusters.items():
            if node_id in nodes:
                return cluster_id
        return None