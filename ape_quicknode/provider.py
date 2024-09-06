import os
from collections.abc import Iterable
from typing import Any, Optional
from pydantic import BaseModel, Field
from ape.api import ReceiptAPI, TraceAPI, TransactionAPI, UpstreamProvider
from ape.exceptions import (
    APINotImplementedError,
    ContractLogicError,
    ProviderError,
    VirtualMachineError,
)
from ape.types import BlockID
from ape_ethereum.provider import Web3Provider
from ape_ethereum.transactions import AccessList
from eth_typing import HexStr
from requests import HTTPError
from web3 import HTTPProvider, Web3
from web3.exceptions import ContractLogicError as Web3ContractLogicError
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware
from web3.types import RPCEndpoint

from .constants import QUICKNODE_NETWORKS
from .exceptions import QuickNodeFeatureNotAvailable, QuickNodeProviderError, MissingAuthTokenError
from .trace import QuickNodeTransactionTrace

DEFAULT_ENVIRONMENT_VARIABLE_NAMES = ("QUICKNODE_SUBDOMAIN", "QUICKNODE_AUTH_TOKEN")

NETWORKS_SUPPORTING_WEBSOCKETS = ("ethereum", "arbitrum", "base", "optimism", "polygon")

class QuickNode(Web3Provider, UpstreamProvider, BaseModel):
    name: str = Field(default="QuickNode")

    def __init__(self, network: Any, name: str = "QuickNode", **data):
        super().__init__(network=network, name=name, **data)
        self._web3 = None
        self.network_uris = {}
        
    @property
    def provider_name(self) -> str:
        return self.name
        
    network_uris: dict[tuple, str] = {}

    @property
    def uri(self):
        """
        QuickNode RPC URI, including the subdomain and auth token.
        """
        ecosystem_name = self.network.ecosystem.name
        network_name = self.network.name
        if (ecosystem_name, network_name) in self.network_uris:
            return self.network_uris[(ecosystem_name, network_name)]

        subdomain = os.environ.get("QUICKNODE_SUBDOMAIN")
        auth_token = os.environ.get("QUICKNODE_AUTH_TOKEN")

        if not subdomain or not auth_token:
            raise MissingAuthTokenError(DEFAULT_ENVIRONMENT_VARIABLE_NAMES)

        if ecosystem_name not in QUICKNODE_NETWORKS or network_name not in QUICKNODE_NETWORKS[ecosystem_name]:
            raise ProviderError(f"Unsupported network: {ecosystem_name} - {network_name}")

        uri_template = QUICKNODE_NETWORKS[ecosystem_name][network_name]
        uri = uri_template.format(subdomain=subdomain, auth_token=auth_token)
        self.network_uris[(ecosystem_name, network_name)] = uri
        return uri

    @property
    def http_uri(self) -> str:
        return self.uri

    @property
    def ws_uri(self) -> str:
        return "ws" + self.uri[5:]

    @property
    def priority_fee(self) -> int:
        if self.network.ecosystem.name == "polygon-zkevm":
            raise APINotImplementedError()
        return super().priority_fee

    @property
    def connection_str(self) -> str:
        return self.uri

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))
        try:
            if self.network.ecosystem.name in ["optimism", "base", "polygon"]:
                self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

            self._web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        except Exception as err:
            raise ProviderError(f"Failed to connect to QuickNode.\n{repr(err)}") from err

    def disconnect(self):
        self._web3 = None

    def _get_prestate_trace(self, transaction_hash: str) -> dict:
        return self.make_request(
            "debug_traceTransaction", [transaction_hash, {"tracer": "prestateTracer"}]
        )

    def get_transaction_trace(self, transaction_hash: str, **kwargs) -> TraceAPI:
        if not transaction_hash.startswith("0x"):
            raise QuickNodeProviderError("Transaction hash must be a hexadecimal string starting with '0x'")
        
        return QuickNodeTransactionTrace(transaction_hash=transaction_hash, provider=self, **kwargs)

    def get_virtual_machine_error(self, exception: Exception, **kwargs) -> VirtualMachineError:
        txn = kwargs.get("txn")
        if not hasattr(exception, "args") or not len(exception.args):
            return VirtualMachineError(base_err=exception, txn=txn)

        args = exception.args
        message = args[0]
        if (
            not isinstance(exception, Web3ContractLogicError)
            and isinstance(message, dict)
            and "message" in message
        ):
            return VirtualMachineError(message["message"], txn=txn)

        elif not isinstance(message, str):
            return VirtualMachineError(base_err=exception, txn=txn)

        message_prefix = "execution reverted"
        if message.startswith(message_prefix):
            message = message.replace(message_prefix, "")

            if ":" in message:
                message = message.split(":")[-1].strip()
                return ContractLogicError(revert_message=message, txn=txn)
            else:
                return ContractLogicError(txn=txn)

        return VirtualMachineError(message=message, txn=txn)

    def create_access_list(
        self, transaction: TransactionAPI, block_id: Optional[BlockID] = None
    ) -> list[AccessList]:
        if self.network.ecosystem.name == "polygon-zkevm":
            raise APINotImplementedError()

        return super().create_access_list(transaction, block_id=block_id)

    def make_request(self, rpc: str, parameters: Optional[Iterable] = None) -> Any:
        parameters = parameters or []
        try:
            result = self.web3.provider.make_request(RPCEndpoint(rpc), parameters)
        except HTTPError as err:
            response_data = err.response.json() if err.response else {}
            if "error" not in response_data:
                raise QuickNodeProviderError(str(err)) from err

            error_data = response_data["error"]
            message = (
                error_data.get("message", str(error_data))
                if isinstance(error_data, dict)
                else error_data
            )
            cls = (
                QuickNodeFeatureNotAvailable
                if "is not available" in message
                else QuickNodeProviderError
            )
            raise cls(message) from err

        if isinstance(result, dict) and (res := result.get("result")):
            return res

        return result

    def get_receipt(
        self,
        txn_hash: str,
        required_confirmations: int = 0,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> ReceiptAPI:
        if not required_confirmations and not timeout:
            data = self.web3.eth.get_transaction_receipt(HexStr(txn_hash))
            txn = dict(self.web3.eth.get_transaction(HexStr(txn_hash)))
            return self.network.ecosystem.decode_receipt(
                {
                    "provider": self,
                    "required_confirmations": required_confirmations,
                    **txn,
                    **data,
                }
            )
        return super().get_receipt(
            txn_hash, required_confirmations=required_confirmations, timeout=timeout, **kwargs
        )