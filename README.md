# Blockchain Simulation Environment with HRB Consensus Mechanism

This repository provides a simulation environment for blockchain networks, implementing a novel consensus mechanism called **Hierarchical Reputation-Based Consensus (HRBC)** algorithm. HRBC is consensus mechanism designed to improve Byzantine Fault Tolerance by addressing the limitations of Practical Byzantine Fault Tolerance (PBFT).  

## Features
- **Blockchain Simulation**: A modular environment for testing blockchain behavior.
- **HRBC Consensus Algorithm**: An innovative approach leveraging hierarchical clustering and reputation-based mechanisms for fault tolerance.
- **Cluster Formation**: Nodes are grouped into clusters based on dynamic parameters like reputation, uptime, and network proximity.
- **Super Node Selection**: Cluster leaders and a super node are chosen to enhance decision-making efficiency.
- **Reputation Decay and Penalty System**: Ensures dynamic and fair governance among participating nodes.
- **Pluggable Architecture**: Extend or replace the consensus algorithm for experimentation and research.

## Why HRBC?
The HRBC consensus algorithm is designed to:
1. Address PBFT scalability limitations in large blockchain networks.
2. Enhance fault tolerance and reduce the impact of malicious nodes.
3. Introduce a reputation-based model that incentivizes honest behavior.

## Getting Started

### Prerequisites
- Python 3.8+
- Required libraries (install via `requirements.txt`)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/blockchain-sim-hrbc-consensus.git
   cd blockchain-sim-hrbc-consensus
   ```
2. Install dependencies
    ```bash
    pip install -r requirements.txt
    ```
### Running the Simulation

#### 1. Set the Number of Nodes
- Open the client.py and deploy_nodes.py files in your preferred editor.
- Locate the number_of_nodes variable in both files and set it to the desired number of nodes for your simulation.

#### 2. Deploy nodes
    ```bash
    python deploy_nodes.py
    ```
#### 3. Start a transaction:  
Once the nodes are deployed, initiate transactions by running  

    ```bash
    python client.py
    ```

#### 4. Verify the Transaction and Blockchain Update  
To confirm the success of the transaction and the addition of a new block visit `localhost:5001/sync_blockchain` in your browser and check if a new block has been added to the blockchain, alongside the genesis block.