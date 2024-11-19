# app.py

import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from blockchain import Blockchain
from node_communication import broadcast_block
from zkp import verify_proof, challenge_verifier, issue_token, verify_token
from config import CURRENT_NODE_URL, DIFFICULTY_LEVEL
from block import Block
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        # Uncomment the next line to also log to a file
        # logging.FileHandler(os.path.join(data_dir, 'node.log'))
    ]
)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST"], "allow_headers": "*"}})

# Ensure correct number of arguments
if len(sys.argv) < 3:
    logging.error("Usage: python app.py <port> <data_dir>")
    sys.exit(1)

port = int(sys.argv[1])
data_dir = sys.argv[2]

# Initialize the blockchain with unique node_id and data_dir
node_id = f'node_{port}'
blockchain = Blockchain(consensus_algorithm='HRBC', node_id=node_id, data_dir=data_dir)

@app.route('/register', methods=['POST'])
def register():
    logging.debug("Entered /register endpoint")
    try:
        data = request.get_json()
        logging.debug(f"Received registration data: {data}")

        if not data or 'userId' not in data or 'hashedPassword' not in data:
            logging.warning("Invalid input for registration.")
            return jsonify({"message": "Invalid input"}), 400  # Bad Request
        
        user_id = data['userId']
        hashed_password = data['hashedPassword']

        # Check if user is already registered
        if user_id in blockchain.user_db:
            logging.warning(f"User {user_id} already registered.")
            return jsonify({"message": "User already registered"}), 400

        # Register the user
        blockchain.user_db[user_id] = hashed_password
        logging.info(f"User {user_id} registered successfully.")

        new_block, consensus_id = blockchain.add_block(user_id, {"action": "register"}, None)
        logging.debug(new_block)

        if new_block:
            logging.info(f"New block created: {new_block}")
            broadcast_block(blockchain.peer_nodes, block=new_block, consensus_id=consensus_id)
            return jsonify({"message": "Registration successful", "block": new_block.__dict__}), 200
        else:
            logging.error("Failed to add registration block.")
            return jsonify({"message": "Failed to add registration block"}), 500

    except Exception as e:
        logging.error(f"Error during registration: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/initiate_zkp', methods=['POST'])
def initiate_zkp():
    logging.debug("Entered /initiate_zkp endpoint")
    try:
        data = request.get_json()
        user_id = data['userId']
        logging.debug(f"Received initiate_zkp data: {data}")

        if user_id not in blockchain.user_db:
            logging.warning(f"User {user_id} not registered.")
            return jsonify({"message": "User not registered"}), 404

        T = data['T']
        q = blockchain.p - 1
        c = challenge_verifier(q)

        blockchain.user_db[user_id + '_T'] = T
        logging.info(f"Commitment T stored for user {user_id}.")

        # new_block, consensus_id = blockchain.add_block(user_id, {"action": "initiation_zkp"}, None)

        return jsonify({"challenge": c}), 200

        # if new_block:
        #     broadcast_block(blockchain.peer_nodes, block=new_block, consensus_id=consensus_id)
        #     return jsonify({"challenge": c}), 200
        # else:
        #     return jsonify({"message": "Failed to add registration block"}), 500
            
    except Exception as e:
        logging.error(f"Error during Initiation: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/verify_zkp', methods=['POST'])
def verify_zkp():
    logging.debug("Entered /verify_zkp endpoint")
    try:
        data = request.get_json()
        user_id = data['userId']
        s = data['s']
        c = data['challenge']
        node_id = request.host
        logging.debug(f"Received verify_zkp data: {data}")

        if user_id not in blockchain.user_db or user_id + '_T' not in blockchain.user_db:
            logging.warning(f"User {user_id} not registered or commitment not found.")
            return jsonify({"message": "User not registered or commitment not found"}), 404

        T = blockchain.user_db[user_id + '_T']
        H_f = blockchain.user_db[user_id]
        C = pow(blockchain.g, H_f, blockchain.p)

        if verify_proof(s, T, C, c, blockchain.p, blockchain.g):
            token = issue_token(user_id, node_id)
            if user_id not in blockchain.issued_tokens:
                blockchain.issued_tokens[user_id] = []
            blockchain.issued_tokens[user_id].append(token)
            logging.info(f"ZKP verified for user {user_id}. Token issued: {token}")
            # new_block, consensus_id = blockchain.add_block(user_id, {"action": "verification_zkp"}, None)
            return jsonify({"message": "Login successful", "token": token}), 200
        else:
            logging.warning(f"ZKP verification failed for user {user_id}.")
            return jsonify({"message": "Login failed"}), 401

        # if new_block:
        #     broadcast_block(blockchain.peer_nodes, block=new_block, consensus_id=consensus_id)
        #     return jsonify({"message": "Login successful", "token": token}), 200
        # else:
        #     return jsonify({"message": "Login failed"}), 401

    except Exception as e:
        logging.error(f"Error during Verification: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/authenticate', methods=['POST'])
def authenticate():
    logging.debug("Entered /authenticate endpoint")
    try:
        data = request.get_json()
        user_id = data['userId']
        tokens = data['tokens']
        logging.debug(f"Received authenticate data: {data}")

        valid_tokens = 0
        for token in tokens:
            decoded_token = verify_token(token)
            if decoded_token and decoded_token['user_id'] == user_id:
                valid_tokens += 1

        if valid_tokens > len(blockchain.peer_nodes) // 2:
            logging.info(f"Authentication successful for user {user_id}. Valid tokens: {valid_tokens}")
            return jsonify({"message": "Authentication successful"}), 200
        else:
            logging.warning(f"Authentication failed for user {user_id}. Valid tokens: {valid_tokens}")
            return jsonify({"message": "Authentication failed"}), 401

    except Exception as e:
        logging.error(f"Error during Authentication: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/process_request', methods=['POST'])
def process_request():
    logging.debug("Entered /process_request endpoint")
    try:
        data = request.get_json()
        user_id = data['userId']
        tokens = data['tokens']
        logging.debug(f"Received process_request data: {data}")

        # Verify if a majority of tokens are valid
        valid_tokens = 0
        for token in tokens:
            decoded_token = verify_token(token)
            if decoded_token and decoded_token['user_id'] == user_id:
                valid_tokens += 1

        if valid_tokens > len(blockchain.peer_nodes) // 2:
            # Broadcast to other nodes that the request is valid
            logging.info(f"Processing request for user {user_id}. Broadcasting to peers.")
            for node in blockchain.peer_nodes:
                broadcast_block(node, {"user_id": user_id, "action": "process"}, consensus_id=blockchain.id)
            return jsonify({"message": "Request processed successfully"}), 200
        else:
            logging.warning(f"Request denied for user {user_id}. Valid tokens: {valid_tokens}")
            return jsonify({"message": "Request denied"}), 401

    except Exception as e:
        logging.error(f"Error during Process Request: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/add_block', methods=['POST'])
def add_block():
    logging.debug("Entered /add_block endpoint")
    try:
        block_data = request.get_json()
        user_id = block_data.get('user_id')
        transaction = block_data.get('transaction')
        commitment = block_data.get('commitment')
        logging.debug(f"Received add_block data: {block_data}")

        new_block, consensus_id = blockchain.add_block(user_id, transaction, commitment)
        if new_block:
            # Broadcast the new block to peer nodes
            logging.info(f"Adding new block for user {user_id} and broadcasting to peers.")
            broadcast_block(blockchain.peer_nodes, new_block, consensus_id=consensus_id)
            return jsonify({"message": "Block added", "block": new_block.__dict__}), 200
        else:
            logging.error("Failed to add block.")
            return jsonify({"message": "Failed to add block"}), 400

    except Exception as e:
        logging.error(f"Error during Add Block: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/sync_blockchain', methods=['GET'])
def sync_blockchain():
    logging.debug("Entered /sync_blockchain endpoint")
    try:
        chain_data = [block.__dict__ for block in blockchain.chain]
        logging.debug(f"Syncing blockchain data: {chain_data}")
        return jsonify(chain_data), 200
    except Exception as e:
        logging.error(f"Error during Sync Blockchain: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/metrics', methods=['GET'])
def get_metrics():
    logging.debug("Entered /metrics endpoint")
    try:
        metrics = blockchain.metrics
        logging.debug(f"Returning metrics: {metrics}")
        return jsonify(metrics), 200
    except Exception as e:
        logging.error(f"Error during Get Metrics: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/receive_block', methods=['POST'])
def receive_block():
    logging.debug("Entered /receive_block endpoint")
    try:
        block_data = request.get_json()
        consensus_id = block_data.get('consensus_node')
        logging.debug(f"Received block data: {block_data}")

        new_block = Block(
            block_data['user_id'],
            block_data['previous_hash'],
            block_data['transaction'],
            block_data['commitment'],
            block_data.get('timestamp'),
            block_data.get('nonce', 0),
        )
        logging.debug(f"Constructed new block: {new_block}")

        if blockchain.consensus.validate_block(blockchain, new_block, consensus_id):
            blockchain.consensus.process_new_block(blockchain, new_block)
            logging.info(f"Block added successfully from node {consensus_id}.")
            return jsonify({"message": "Block added successfully"}), 200
        else:
            logging.error("Invalid block received.")
            return jsonify({"message": "Invalid block"}), 400

    except Exception as e:
        logging.error(f"Error during Receive Block: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/select_node', methods=['POST'])
def select_node():
    logging.debug("Entered /select_node endpoint")
    try:
        data = request.get_json()
        node_id = data.get('consensus_id')
        stop_time = data.get('stop_time')
        logging.debug(f"Received select_node data: {data}")
        
        if node_id:
            logging.info(f"Received selection completion notification with ID: {node_id}")
            # Implement the logic to stop mining here
            blockchain.consensus.stop_selection(stop_time)
            return jsonify({"message": "Mining Stopped"}), 200
        else:
            logging.warning("No ID provided in select_node request.")
            return jsonify({"error": "No ID provided."}), 400

    except Exception as e:
        logging.error(f"Error during Select Node: {e}")
        logging.debug(traceback.format_exc())  # Detailed traceback
        return jsonify({"message": "Internal Server Error", "error": str(e)}), 500

@app.route('/set_params', methods=['POST'])
def set_params():
    logging.debug("Entered /set_params endpoint")
    # Implement parameter setting logic here
    return jsonify({"message": "Parameters set successfully"}), 200    

# app.py
from block import Block  # Make sure Block is imported

@app.route('/vote_on_block', methods=['POST'])
def vote_on_block():
    try:
        data = request.get_json()
        block_data = data.get('block')

        if block_data:
            try:
                # Exclude 'hash' from block_data before creating Block object
                block_data_without_hash = block_data.copy()  # Create a copy to avoid modifying original data
                block_data_without_hash.pop('hash', None)  # Safely remove 'hash' if present
                
                block = Block(**block_data_without_hash)
                
            except TypeError as e:
                logging.error(f"Error creating block from JSON: {e}, Block Data: {block_data_without_hash}")
                return jsonify({'error': 'Invalid block data'}), 400
        else:
            logging.error("No 'block' data received in request.")
            return jsonify({'error': 'Invalid request data'}), 400

        vote = blockchain.consensus.vote_on_block(block)
        logging.debug(f"Vote requested for block: {block.hash}, Vote: {vote}")
        return jsonify({'vote': vote}), 200

    except Exception as e:
        logging.error(f"Error during voting: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    

if __name__ == '__main__':
    # Default to port 5000 if no argument is given
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    logging.info(f"Starting Flask server on port {port}")
    app.run(port=port, debug=True, use_reloader=False)  # Disable reloader for consistent logging
