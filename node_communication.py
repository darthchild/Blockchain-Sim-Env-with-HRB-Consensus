
# node_communication.py

import requests
from config import AUTHORITY_NODE_URL
import logging

def sync_blockchain():
    logging.debug("Attempting to synchronize blockchain with authority node.")
    try:
        response = requests.get(f'{AUTHORITY_NODE_URL}/sync_blockchain')
        response.raise_for_status()  # Raise an exception for HTTP errors
        chain = response.json()
        logging.info(f"Synchronized blockchain: {chain}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during blockchain synchronization: {e}")
        logging.debug("Traceback:", exc_info=True)

def broadcast_block(peer_nodes, block, consensus_id):
    logging.debug(f"Broadcasting block to peers: {peer_nodes} with consensus_id: {consensus_id}")
    block_data = {
        'user_id': block.user_id,
        'previous_hash': block.previous_hash,
        'transaction': block.transaction,
        'nonce': block.nonce,
        'commitment': block.commitment,
        'timestamp': block.timestamp,
        'consensus_node': consensus_id,
    }

    for node in peer_nodes:
        try:
            response = requests.post(f'http://{node}/receive_block', json=block_data, timeout=100)
            response.raise_for_status()  # Raise an exception for HTTP errors
            logging.info(f"Block broadcasted to {node}")
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"Failed to broadcast block to {node}. HTTP Error: {http_err.response.status_code} - {http_err.response.reason}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error broadcasting to {node}: {e}")
            logging.debug("Traceback:", exc_info=True)

def broadcast_node_selection_complete(peer_nodes, consensus_id, stop_time):
    logging.debug(f"Broadcasting node selection completion to peers: {peer_nodes} with consensus_id: {consensus_id}")
    for node in peer_nodes:
        url = f'http://{node}/select_node'
        payload = {'consensus_id': consensus_id, "stop_time": stop_time}
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors

            if response.status_code == 200:
                logging.info(f"Successfully notified {node} to stop mining.")
            else:
                logging.warning(f"Failed to notify {node}. Status Code: {response.status_code} - {response.reason}")
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"Failed to notify {node}. HTTP Error: {http_err.response.status_code} - {http_err.response.reason}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error broadcasting to {node}: {e}")
            logging.debug("Traceback:", exc_info=True)
