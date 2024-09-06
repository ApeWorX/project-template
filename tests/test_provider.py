import re
import pytest
from ape.exceptions import ContractLogicError, ProviderError
from ape.types import LogFilter
from hexbytes import HexBytes
from web3.exceptions import ContractLogicError as Web3ContractLogicError
from ape.api import TraceAPI
from ape_quicknode.trace import QuickNodeTransactionTrace
from ape_quicknode.exceptions import QuickNodeProviderError
from ape_quicknode.exceptions import MissingAuthTokenError, QuickNodeProviderError

TXN_HASH = "0x3cef4aaa52b97b6b61aa32b3afcecb0d14f7862ca80fdc76504c37a9374645c4"

@pytest.fixture
def log_filter():
    return LogFilter(
        address=["0xF7F78379391C5dF2Db5B66616d18fF92edB82022"],
        fromBlock="0x3",
        toBlock="0x3",
        topics=[
            "0x1a7c56fae0af54ebae73bc4699b9de9835e7bb86b050dff7e80695b633f17abd",
            [
                "0x0000000000000000000000000000000000000000000000000000000000000000",
                "0x0000000000000000000000000000000000000000000000000000000000000001",
            ],
        ],
    )

@pytest.fixture
def block():
    return {
        "transactions": [],
        "hash": HexBytes("0xae1960ba0513948a507b652def457305d490d24bc0dd131d8d02be56564a3ee2"),
        "number": 0,
        "parentHash": HexBytes(
            "0x0000000000000000000000000000000000000000000000000000000000000000"
        ),
        "size": 517,
        "timestamp": 1660338772,
        "gasLimit": 30029122,
        "gasUsed": 0,
        "baseFeePerGas": 1000000000,
        "difficulty": 131072,
        "totalDifficulty": 131072,
    }

@pytest.fixture
def receipt():
    return {
        "blockNumber": 15329094,
        "data": b"0xa9059cbb00000000000000000000000016b308eb4591d9b4e34034ca2ff992d224b9927200000000000000000000000000000000000000000000000000000000030a32c0",
        "gasLimit": 79396,
        "gasPrice": 14200000000,
        "gasUsed": 65625,
        "logs": [
            {
                "blockHash": HexBytes(
                    "0x141a61b8c738c0f1508728116049a0d4a6ff41ee1180d956148880f32ae99215"
                ),
                "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "logIndex": 213,
                "data": HexBytes(
                    "0x00000000000000000000000000000000000000000000000000000000030a32c0"
                ),
                "removed": False,
                "topics": [
                    HexBytes("0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"),
                    HexBytes("0x000000000000000000000000958f973513f723f2cb9b47abe5e903695ab93e36"),
                    HexBytes("0x00000000000000000000000016b308eb4591d9b4e34034ca2ff992d224b99272"),
                ],
                "blockNumber": 15329094,
                "transactionIndex": 132,
                "transactionHash": HexBytes(
                    "0x9e4be62c1a16caacaccd9d8c7706b75dc17a957ec6c5dea418a137a5c3a197c5"
                ),
            }
        ],
        "nonce": 16,
        "receiver": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "sender": "0x958f973513F723f2cB9b47AbE5e903695aB93e36",
        "status": 1,
        "hash": TXN_HASH,
        "value": 0,
    }

def test_when_no_auth_token_raises_error(missing_token, quicknode_provider):
    with pytest.raises(MissingAuthTokenError) as excinfo:
        quicknode_provider.connect()
    assert "QUICKNODE_SUBDOMAIN" in str(excinfo.value)
    assert "QUICKNODE_AUTH_TOKEN" in str(excinfo.value)
    

def test_send_transaction_reverts(token, quicknode_provider, mock_web3, transaction):
    expected_revert_message = "EXPECTED REVERT MESSAGE"
    mock_web3.eth.send_raw_transaction.side_effect = Web3ContractLogicError(
        f"execution reverted : {expected_revert_message}"
    )
    quicknode_provider._web3 = mock_web3

    with pytest.raises(ContractLogicError, match=expected_revert_message):
        quicknode_provider.send_transaction(transaction)

def test_send_transaction_reverts_no_message(token, quicknode_provider, mock_web3, transaction):
    mock_web3.eth.send_raw_transaction.side_effect = Web3ContractLogicError("execution reverted")
    quicknode_provider._web3 = mock_web3

    with pytest.raises(ContractLogicError, match="Transaction failed."):
        quicknode_provider.send_transaction(transaction)

def test_estimate_gas_would_revert(token, quicknode_provider, mock_web3, transaction):
    expected_revert_message = "EXPECTED REVERT MESSAGE"
    mock_web3.eth.estimate_gas.side_effect = Web3ContractLogicError(
        f"execution reverted : {expected_revert_message}"
    )
    quicknode_provider._web3 = mock_web3

    with pytest.raises(ContractLogicError, match=expected_revert_message):
        quicknode_provider.estimate_gas_cost(transaction)

def test_estimate_gas_would_revert_no_message(token, quicknode_provider, mock_web3, transaction):
    mock_web3.eth.estimate_gas.side_effect = Web3ContractLogicError("execution reverted")
    quicknode_provider._web3 = mock_web3

    with pytest.raises(ContractLogicError, match="Transaction failed."):
        quicknode_provider.estimate_gas_cost(transaction)

def test_get_contract_logs(networks, quicknode_provider, mock_web3, block, log_filter):
    mock_web3.eth.get_block.return_value = block
    quicknode_provider._web3 = mock_web3
    networks.active_provider = quicknode_provider
    actual = [x for x in quicknode_provider.get_contract_logs(log_filter)]

    assert actual == []

def test_unsupported_network(quicknode_provider, monkeypatch):
    monkeypatch.setenv("QUICKNODE_SUBDOMAIN", "test_subdomain")
    monkeypatch.setenv("QUICKNODE_AUTH_TOKEN", "test_token")
    quicknode_provider.network.ecosystem.name = "unsupported_ecosystem"
    quicknode_provider.network.name = "unsupported_network"

    with pytest.raises(ProviderError, match="Unsupported network:"):
        quicknode_provider.uri

def test_quicknode_provider_error(quicknode_provider, mock_web3):
    error_message = "QuickNode API error"
    mock_web3.provider.make_request.side_effect = QuickNodeProviderError(error_message)
    quicknode_provider._web3 = mock_web3

    with pytest.raises(QuickNodeProviderError, match=error_message):
        quicknode_provider.make_request("eth_blockNumber", [])
        
def test_get_transaction_trace(networks, quicknode_provider, mock_web3, receipt):
    tx_hash = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    mock_trace_data = {
        "output": "0x",
        "gasUsed": "0x5208",
        "revertReason": None,
    }
    mock_web3.provider.make_request.return_value = mock_trace_data
    mock_web3.eth.wait_for_transaction_receipt.return_value = receipt
    quicknode_provider._web3 = mock_web3
    networks.active_provider = quicknode_provider
    
    trace = quicknode_provider.get_transaction_trace(tx_hash)
    
    assert isinstance(trace, QuickNodeTransactionTrace)
    assert isinstance(trace, TraceAPI)
    assert trace.transaction_hash == tx_hash