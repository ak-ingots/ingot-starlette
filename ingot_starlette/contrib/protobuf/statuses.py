"""The statuses of HTTP of the codes of google.rpc, as AIP-193 maps them."""

__all__ = ("HTTP_STATUSES", "get_http_status")

import typing as t

from google.rpc import code_pb2

HTTP_STATUSES: t.Final[t.Mapping[int, int]] = {
    code_pb2.OK: 200,
    code_pb2.CANCELLED: 499,
    code_pb2.UNKNOWN: 500,
    code_pb2.INVALID_ARGUMENT: 400,
    code_pb2.DEADLINE_EXCEEDED: 504,
    code_pb2.NOT_FOUND: 404,
    code_pb2.ALREADY_EXISTS: 409,
    code_pb2.PERMISSION_DENIED: 403,
    code_pb2.UNAUTHENTICATED: 401,
    code_pb2.RESOURCE_EXHAUSTED: 429,
    code_pb2.FAILED_PRECONDITION: 400,
    code_pb2.ABORTED: 409,
    code_pb2.OUT_OF_RANGE: 400,
    code_pb2.UNIMPLEMENTED: 501,
    code_pb2.INTERNAL: 500,
    code_pb2.UNAVAILABLE: 503,
    code_pb2.DATA_LOSS: 500,
}


def get_http_status(code: int) -> int:
    """The status of HTTP of a code of ``google.rpc.Code``; 500 of an unknown one."""
    return HTTP_STATUSES.get(code, 500)
