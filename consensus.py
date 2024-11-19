# consensus.py

from abc import ABC, abstractmethod

class Consensus(ABC):
    @abstractmethod
    def validate_block(self, blockchain, new_block, consensus_id):
        pass

    @abstractmethod
    def process_new_block(self, blockchain, new_block):
        pass

