# poa_consensus.py

from consensus import Consensus

class PoAConsensus(Consensus):
    def mine_block(self, blockchain, block_data):
        """In POA, a predefined authority node creates the block."""
        if not blockchain.authorized_nodes:
            raise Exception("No authorized nodes available to create blocks.")
        # For simplicity, select the next authorized node in a round-robin fashion
        validator = blockchain.authorized_nodes[0]  # Simplistic approach
        print(f"Block created by authority node: {validator}")
        block_data['validator'] = validator
        block_hash = self.calculate_hash(block_data)
        return {'validator': validator, 'hash': block_hash}

    def process_new_block(self, blockchain, new_block):
        blockchain.chain.append(new_block)

    def calculate_hash(self, block_data):
        block_string = str(block_data).encode()
        return hashlib.sha256(block_string).hexdigest()

    def validate_block(self, blockchain, new_block):
        # Verify that the validator is an authorized node
        if hasattr(new_block, 'validator'):
            if new_block.validator not in blockchain.authorized_nodes:
                print(f"Validator {new_block.validator} is not an authorized node.")
                return False
        else:
            print("No validator specified for the block.")
            return False

        # Additional validation logic can be added here
        # For example, checking the order of authorized nodes, etc.

        # Verify the hash
        expected_hash = self.calculate_hash({
            'user_id': new_block.user_id,
            'previous_hash': new_block.previous_hash,
            'transaction': new_block.transaction,
            'commitment': new_block.commitment,
            'timestamp': new_block.timestamp,
            'validator': new_block.validator
        })
        if new_block.hash != expected_hash:
            print("Block hash mismatch.")
            return False

        return True
