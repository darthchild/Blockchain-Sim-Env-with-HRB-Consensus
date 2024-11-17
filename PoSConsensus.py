import random
from consensus import Consensus
from block import Block

class PoSConsensus(Consensus):
    def __init__(self):
        self.selected_validator = None
        self.reward = 10

    def select_validator(self, blockchain):
        """Deterministically select a validator based on stake and last block hash."""
        total_stake = sum(blockchain.reputation_tokens.values())
        if total_stake == 0:
            print("No reputation tokens in the system.")
            return None

        # Use the hash of the last block to generate a seed
        last_block_hash = blockchain.get_last_block().hash
        seed = int(last_block_hash, 16)
        random.seed(seed)

        # Build a list of nodes sorted to ensure consistency
        nodes = sorted(blockchain.reputation_tokens.keys())
        cumulative_reputation_tokens = []
        cumulative = 0

        for node in nodes:
            cumulative += blockchain.reputation_tokens[node]
            cumulative_reputation_tokens.append((cumulative, node))

        # Generate a random number and select the validator
        r = random.uniform(0, total_stake)
        for cumulative, node in cumulative_reputation_tokens:
            if r <= cumulative:
                self.selected_validator = node
                break

        print(f"Selected validator: {self.selected_validator}")

    def node_select(self, user_id, last_block, transaction, commitment, block_data, blockchain):
        """Determine if the current node is selected to create the block."""
        self.select_validator(blockchain)
        if blockchain.id == self.selected_validator:
            # Current node is the selected validator
            new_block = Block(user_id, last_block.hash, transaction, commitment)
            return new_block, blockchain.id
        else:
            print(f"Node {self.selected_validator} has been selected as validator. Current node {blockchain.id} not selected.")
            return None, None

    def validate_block(self, blockchain, new_block, consensus_id):
        """Validate the block proposed by the selected validator."""
        last_block = blockchain.get_last_block()
        if new_block.previous_hash != last_block.hash:
            print("Invalid previous hash.")
            return False
        if new_block.hash != new_block.calculate_hash():
            print("Invalid block hash.")
            return False
        # Update reputation tokens
        blockchain.reputation_tokens[consensus_id] += self.reward
        return True

    def process_new_block(self, blockchain, new_block):
        """Add the valid block to the blockchain."""
        blockchain.chain.append(new_block)
        print(f"Block added by {new_block.user_id} to the blockchain.")
        print(blockchain.reputation_tokens)

        blockchain.update_metrics(new_block)

    def stop_selection(self):
        """No process to stop in PoS consensus."""
        pass
