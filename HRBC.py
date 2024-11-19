# hrbc.py
import hashlib
import json
import time
import random
import requests
from consensus import Consensus
from block import Block
import logging


class HRBC(Consensus):
    def __init__(self, blockchain):
        super().__init__()
        self.blockchain = blockchain  # Ref to the blockchain object
        self.node_properties = self.initialize_node_properties()
        self.clusters = self.form_clusters()
        self.cluster_leaders = self.elect_cluster_leaders()
        self.super_node = self.elect_super_node()
        self.reward = 10
        self.penalty = 20 
        self.decay_rate = 0.01  


    def initialize_node_properties(self):
        """Randomly initializes properties for each node."""
        node_properties = {}
        for node_id in self.blockchain.reputation_tokens.keys():
            node_properties[node_id] = {
                'uptime': random.uniform(0.9, 1.0),  
                'network_proximity': random.uniform(0.0, 1.0), 
            }
        logging.debug(f"[HRBC] Node properties initialized: {node_properties}")
        return node_properties


    def initiate_consensus(self, blockchain_instance, user_id, last_block, transactions, commitment):
        node_id = blockchain_instance.id
        cluster_id = self.get_cluster_id(node_id)
        logging.debug(f"[HRBC] initiate_consensus called: node_id={node_id}, cluster_id={cluster_id}, transactions={transactions}")

        if cluster_id is not None:
            if node_id == self.cluster_leaders[cluster_id]:  # Leader initiates consensus
                proposed_block = self.create_block(user_id, last_block.hash, transactions, commitment)
                logging.debug(f"[HRBC] Proposed block created: {proposed_block}")

                if proposed_block:
                    consensus_result = self.perform_inter_cluster_consensus(blockchain_instance, proposed_block)
                    if consensus_result:
                        self.last_consensus_id = blockchain_instance.id
                        logging.info(f"[HRBC] Consensus achieved. Block: {proposed_block}") # Log successful consensus
                        return proposed_block
                    else:
                        return None
                else:
                    logging.warning("[HRBC] Block creation failed.")
                    return None  # Or handle the failure appropriately


            else: # Member waits for the leader to propose the block.
                return None # If not leader, return None immediately and wait for a broadcasted block.
        else:
            logging.warning(f"[HRBC] Node {node_id} not part of any cluster.")
            return None # Or handle the failure as neede

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

    def vote_on_block(self, block):
        """Votes on a block based on simplified validation."""  # Simplified logic
        # In a real implementation, you'll have more sophisticated validation checks
        # ... Add any necessary validation logic
        is_valid = random.random() < 0.8  # Simulate a validation check (80% success rate)
        logging.debug(f"[HRBC] Node {self.blockchain.id} voted {'YES' if is_valid else 'NO'} on block {block.hash}")
        return is_valid  # Return True if valid, False otherwise


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
    
    def perform_inter_cluster_consensus(self, blockchain_instance, proposed_block):
        """Performs inter-cluster consensus using majority voting."""

        positive_votes = 0
        total_cluster_leaders = len(self.cluster_leaders)
        two_thirds_majority = (2 * total_cluster_leaders) // 3 # calculate the 2/3rd's majority

        #Collect votes from all cluster leaders
        for cluster_id, leader_id in self.cluster_leaders.items():
            if leader_id != blockchain_instance.id:  # Exclude self (already positive vote as the proposer)
                vote = self.request_vote(leader_id, proposed_block)
                logging.debug(f"[HRBC] Vote received from {leader_id}: {vote}")
                if vote:
                    positive_votes += 1


        # Check if 2/3rds majority is reached
        if positive_votes >= two_thirds_majority -1: # Minus 1 for current node
            logging.info("[HRBC] Inter-cluster consensus achieved.")
            return True  # Consensus achieved
        logging.warning("[HRBC] Inter-cluster consensus failed.")
        return False # Consensus failed


    def request_vote(self, node_id, block):
        """Requests a vote from another cluster leader."""
        url = f'http://{self.get_node_url(node_id)}/vote_on_block' # Use appropriate URL
        data = {'block': block.__dict__}  # Send necessary block information
        try:
            response = requests.post(url, json=data, timeout=5) # Send vote request. Timeout after 5 seconds
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()['vote'] # Return the vote from other node.
        except requests.exceptions.RequestException as e: # Catch any exceptions during communication
            logging.error(f"[HRBC] Error requesting vote from {node_id}: {e}")
            logging.debug(traceback.format_exc())  # Detailed traceback
            return False  # Treat communication errors as negative votes

    def get_node_url(self, node_id):
       """Gets the URL for a given node ID."""
       # Implement the logic to find the node's URL based on the node_id.
       #Modify this according to how your nodes' URLs are structured.
       for peer in self.blockchain.peer_nodes:
           if node_id.split('_')[1] == peer.split(':')[1]:
               return peer
       return None