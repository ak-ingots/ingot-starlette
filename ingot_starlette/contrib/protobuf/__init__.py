"""
The services of protobuf over HTTP, of JSON, by the extra ``protobuf``:
their methods transcoded by the annotations ``google.api.http`` of their
contract (AIP-127), the request and the reply the canonical JSON of their
messages, the statuses of the codes of google.rpc those of AIP-193. It
needs protobuf alone, no grpcio: the handlers are the addon's, the same
RPCs its servicers of gRPC run, so that both transports answer alike.
"""

__all__ = (
    "HTTP_STATUSES",
    "BaseStarletteProtobufEndpoint",
    "HttpRule",
    "StarletteProtobufRpc",
    "get_http_rule",
    "get_http_status",
)

from .endpoints import BaseStarletteProtobufEndpoint, StarletteProtobufRpc
from .rules import HttpRule, get_http_rule
from .statuses import HTTP_STATUSES, get_http_status
