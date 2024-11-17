# config.py

CURRENT_NODE_URL = "http://localhost:5000"
AUTHORITY_NODE_URL = "http://localhost:5000"

# Cryptographic Parameters
P = 29
G = 5

DIFFICULTY_LEVEL = 4

# JWT Secret Key
SECRET_KEY = "secret-key-for-tokens"

# Authorized Nodes for PoA (Only relevant for PoA)
AUTHORIZED_NODES = ["node1", "node2"]  # Example authority nodes
