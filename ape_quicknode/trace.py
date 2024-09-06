from functools import cached_property
from typing import Any, Optional
from ape_ethereum.trace import TraceApproach, TransactionTrace
from hexbytes import HexBytes

class QuickNodeTransactionTrace(TransactionTrace):
    call_trace_approach: TraceApproach = TraceApproach.PARITY

    @cached_property
    def return_value(self) -> Any:
        node = self._top_level_call
        if output := node.get("output"):
            output_bytes = HexBytes(output)
            if abi := self.root_method_abi:
                return self._ecosystem.decode_returndata(abi, output_bytes)

            return output_bytes

        return None

    @cached_property
    def revert_message(self) -> Optional[str]:
        node = self._top_level_call
        return node.get("revertReason")

    @cached_property
    def _top_level_call(self) -> dict:
        return self.provider.make_request(
            "debug_traceTransaction",
            [
                self.transaction_hash,
                {"tracer": "callTracer", "tracerConfig": {"onlyTopLevelCall": True}},
            ],
        )