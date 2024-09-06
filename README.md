
# QuickNode Ape Plugin

Use the [QuickNode](https://www.quicknode.com/) provider plugin to interact with blockchains via QuickNode's APIs.

If you don't have a QuickNode account already, you can create one [here](https://www.quicknode.com/signup?utm_source=internal&utm_campaign=ape-plugin&utm_content=quicknode-ape-plugin).

## Supported Networks

The `ape-quicknode` plugin supports the following ecosystems:

- Ethereum
- Arbitrum
- Base
- Optimism
- Polygon
- Polygon-ZkEVM

## Dependencies

- [python3](https://www.python.org/downloads) version 3.9 up to 3.12.

## Installation

### via `pip`

You can install the latest release via [`pip`](https://pypi.org/project/pip/):

```bash
pip install ape-quicknode
```

### via setuptools

You can clone the repository and use setuptools for the most up-to-date version:

```bash
git clone https://github.com/your-username/ape-quicknode.git
cd ape-quicknode
python3 setup.py install
```

## Configuration

To use the QuickNode provider, you need to set up your QuickNode credentials. You can do this by setting environment variables.

### Environment Variables

Set the following environment variables:

```bash
export QUICKNODE_SUBDOMAIN=your-quicknode-subdomain
export QUICKNODE_AUTH_TOKEN=your-quicknode-auth-token
```

## Usage

### Command Line

To use the QuickNode provider plugin in most commands, set it via the --network option:

```bash
ape console --network ethereum:mainnet:quicknode
```

### Python Script

To connect to QuickNode from a Python script, use the networks top-level manager:

```python
from ape import networks

with networks.ethereum.mainnet.use_provider("quicknode") as provider:
    # Your code here
    ...
```

### Transaction Traces

You can access transaction traces using the QuickNode provider:

```python
from ape import networks

quicknode = networks.provider  # Assuming connected to QuickNode
txn_hash = "0x45a8ab098ef27f028afe532f3ca241a3425725093f1302c9bf14a03993891b70"  # Replace the hash with another hash if needed or using another network
trace = quicknode.get_transaction_trace(txn_hash)
print(f"Raw call tree: {trace.get_raw_calltree()}")
```

## Testing

### CLI Testing

You can test the QuickNode provider functionality directly from the Ape console. Here's a step-by-step guide:

1. Initialize the Ape console with QuickNode provider:

```bash
ape console --network ethereum:mainnet:quicknode
```

2. Once in the console, you can make various calls to test the functionality:

```bash
# Get the latest block number
networks.provider.get_block('latest').number

# Get the current network gas price
networks.provider.gas_price

# Get a transaction by its hash
tx_hash = "0x45a8ab098ef27f028afe532f3ca241a3425725093f1302c9bf14a03993891b70" # Replace the hash with another hash if needed or using another network
networks.provider.get_transaction(tx_hash)

# Get a transaction receipt
networks.provider.get_receipt(tx_hash)

# Get a transaction trace
networks.provider.get_transaction_trace(tx_hash).get_raw_calltree()
```

### Unit Tests

To run the unit tests for the QuickNode plugin:

```bash
pytest tests/
```

## Development

To set up the development environment:

1. Clone the repository
2. Install the development dependencies:

```bash
pip install -e ".[dev]"
```

3. Install the pre-commit hooks:

```bash
pre-commit install
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache 2.0 License.
