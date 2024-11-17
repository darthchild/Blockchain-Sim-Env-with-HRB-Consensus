# deploy_nodes.py

import subprocess
import sys
import time
import os
import signal

node_processes = []  # List to keep track of all node processes

def generate_peers_file(node_port, starting_port, number_of_nodes, data_dir):
    """Generates a peers.txt file listing all other node addresses."""
    peers = [f"127.0.0.1:{port}" for port in range(starting_port, starting_port + number_of_nodes) if port != node_port]
    peers_file = os.path.join(data_dir, 'peers.txt')
    with open(peers_file, 'w') as f:
        for peer in peers:
            f.write(f"{peer}\n")

def start_node(port, node_id, starting_port, number_of_nodes):
    """Starts a blockchain node on the specified port with unique data directory and logging."""
    try:
        # Create unique data directory for the node
        data_dir = os.path.join('node_data', f'node_{node_id}')
        os.makedirs(data_dir, exist_ok=True)
        
        # Generate peers.txt
        generate_peers_file(port, starting_port, number_of_nodes, data_dir)
        
        # Define log file path
        log_file = os.path.join('logs', f'node_{node_id}.log')
        os.makedirs('logs', exist_ok=True)
        
        # Launch the node process and track it
        with open(log_file, 'w') as f:
            process = subprocess.Popen([sys.executable, 'app.py', str(port), data_dir], stdout=f, stderr=f)
            node_processes.append(process)  # Store process in the list
        
        print(f"Node {node_id} started on port {port} with data directory '{data_dir}' and logging to '{log_file}'")
    except Exception as e:
        print(f"Failed to start node {node_id} on port {port}: {e}")

def main():
    number_of_nodes = 10  # Specify the number of nodes you want to simulate
    starting_port = 5000   # Starting port number
    
    for i in range(number_of_nodes):
        port = starting_port + i
        node_id = f'node_{port}'
        start_node(port, node_id, starting_port, number_of_nodes)
        time.sleep(1)  # Optional: Wait a bit before starting the next node
    
    print(f"Successfully started {number_of_nodes} nodes.")

    try:
        while True:
            time.sleep(1)  # Keep the script running
    except KeyboardInterrupt:
        print("\nShutting down all nodes...")
        for process in node_processes:
            process.terminate()  # Gracefully terminate each node process
            process.wait()       # Wait for the process to finish cleanup
        print("All nodes have been terminated.")

if __name__ == "__main__":
    main()