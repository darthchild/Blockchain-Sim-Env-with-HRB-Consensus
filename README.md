# Blockchain Simulation Environment with HRB Consensus Mechanism

This repository provides a simulation environment for blockchain networks, implementing a novel consensus mechanism called **Hierarchical Reputation-Based Consensus (HRBC)** algorithm. HRBC is consensus mechanism designed to improve Byzantine Fault Tolerance by addressing the limitations of Practical Byzantine Fault Tolerance (PBFT).  

## Getting Started

### Prerequisites
- Python 3.8+
- Required libraries (install via `requirements.txt`)

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/your-username/blockchain-sim-hrbc-consensus.git
   cd blockchain-sim-hrbc-consensus
   ```
2. Install dependencies
    ```
    pip install -r requirements.txt
    ```
### Running the Simulation

#### 1. Set the Number of Nodes
- Open the client.py and deploy_nodes.py files in your preferred editor.
- Locate the number_of_nodes variable in both files and set it to the desired number of nodes for your simulation.

#### 2. Deploy nodes  
   ```
   python deploy_nodes.py
   ```
#### 3. Start a transaction:  
Once the nodes are deployed, initiate transactions by running  
   ```
   python client.py
   ```

#### 4. Verify the Transaction and Blockchain Update  
To confirm the success of the transaction and the addition of a new block visit `localhost:5001/sync_blockchain` in your browser and check if a new block has been added to the blockchain, alongside the genesis block.

## HRBC Algorithm Overview

HRBC is a scalable consensus mechanism designed for permissioned blockchains. It improves upon traditional algorithms like PBFT by using a hierarchical structure to reduce communication overhead and latency.  HRBC's key features include:

* **Cluster-based Architecture:** Nodes are divided into smaller clusters to reduce message complexity.
* **Reputation System:** Nodes are assigned reputation scores based on factors like uptime, validation accuracy, and consensus participation.  This incentivizes honest behavior.
* **Hierarchical Structure:** Cluster leaders are elected based on reputation. Cluster leaders then form a committee to achieve inter-cluster consensus.
* **Super Node:** The cluster leader with the highest reputation acts as a coordinator (Super Node) for inter-cluster consensus. The Super Node does not have any special authority.

## Project Structure

*   **`app.py`:** The Flask application representing a single blockchain node. This is the core node application.
*   **`blockchain.py`:** Implements the core blockchain data structures and logic (adding blocks, managing the chain, and interacting with consensus mechanisms).
*   **`hrbc.py`:** Contains the implementation of the HRBC consensus algorithm. This is the main implementation file for this project.
*   **`block.py`:** Defines the structure of a block in the blockchain.
*   **`node_communication.py`:** Handles communication between nodes (broadcasting blocks).
*   **`config.py`:** Stores global configuration parameters (number of nodes, ports).
*   **`deploy_nodes.py`:** A script to start multiple blockchain nodes simultaneously.
*   **`client.py`:** A script to simulate a client interacting with the blockchain (registration, ZKP, transactions).
