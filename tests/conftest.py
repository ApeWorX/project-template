import os
import pytest
from ape import accounts as ape_accounts
from ape import networks as ape_networks
from ape_quicknode.provider import QuickNode
from requests import HTTPError, Response
from web3 import Web3

@pytest.fixture
def accounts():
    return ape_accounts

@pytest.fixture
def networks():
    return ape_networks

@pytest.fixture
def missing_token(monkeypatch):
    monkeypatch.delenv("QUICKNODE_SUBDOMAIN", raising=False)
    monkeypatch.delenv("QUICKNODE_AUTH_TOKEN", raising=False)

@pytest.fixture
def token(mocker):
    env = os.environ.copy()
    mock = mocker.patch("os.environ.get")

    def side_effect(key, *args, **kwargs):
        if key == "QUICKNODE_SUBDOMAIN":
            return "TEST_SUBDOMAIN"
        elif key == "QUICKNODE_AUTH_TOKEN":
            return "TEST_TOKEN"
        else:
            return env.get(key, *args, **kwargs)

    mock.side_effect = side_effect
    return mock

@pytest.fixture
def mock_web3(mocker):
    mock = mocker.MagicMock(spec=Web3)
    mock.eth = mocker.MagicMock()
    mock.middleware_onion = mocker.MagicMock()
    return mock

@pytest.fixture
def transaction(accounts, networks):
    with networks.ethereum.local.use_provider("test"):
        sender = accounts.test_accounts[0]
        receiver = accounts.test_accounts[1]
        receipt = sender.transfer(receiver, "1 gwei")
        return receipt.transaction

@pytest.fixture
def txn_hash():
    return "0x55d07ce5e3f4f5742f3318cf328d700e43ee8cdb46000f2ac731a9379fca8ea7"

@pytest.fixture(params=[
    "This feature is not available on your current plan. Please upgrade to access this functionality.",
    "This feature is not supported on the current network."
])
def feature_not_available_http_error(mocker, request):
    response = mocker.MagicMock(spec=Response)
    response.fixture_param = request.param
    response.json.return_value = {"error": {"message": request.param}}
    error = HTTPError(response=response)
    return error

@pytest.fixture
def quicknode_provider(networks) -> QuickNode:
    return networks.ethereum.mainnet.get_provider("quicknode")
