# block.py

import hashlib
import json
import time

class Block:
    def __init__(self, user_id, previous_hash, transaction, commitment, timestamp=None, nonce=0):
        self.user_id = user_id
        self.previous_hash = previous_hash
        self.transaction = transaction
        self.commitment = commitment
        self.timestamp = timestamp or time.time()
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Calculate the SHA-256 hash of the block's content."""
        block_string = json.dumps({
            'user_id': self.user_id,
            'previous_hash': self.previous_hash,
            'transaction': self.transaction,
            'nonce': self.nonce,
            'commitment': self.commitment,
            'timestamp': self.timestamp,
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def size_in_bytes(self):
        """Calculate the size of the block in bytes."""
        block_json = json.dumps(self.__dict__, sort_keys=True)
        return len(block_json.encode('utf-8'))

    def __str__(self):
        return json.dumps(self.__dict__, indent=4)
