"""The endpoint transcoding the methods of a service of protobuf to HTTP."""

__all__ = ("BaseStarletteProtobufEndpoint", "StarletteProtobufRpc")

import abc
import json
import typing as t
from dataclasses import dataclass

from google.protobuf import json_format, message_factory
from google.protobuf.descriptor import FieldDescriptor
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.routing import Route

from ingot_starlette.starlette import StarletteEndpoint

from .rules import HttpRule, get_http_rule

if t.TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterator

    from google.protobuf.descriptor import Descriptor, MethodDescriptor
    from google.protobuf.message import Message
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import BaseRoute


@dataclass(frozen=True, slots=True, kw_only=True)
class StarletteProtobufRpc:
    """
    A method of a service of protobuf and its handler over HTTP: the
    request, its message, and the request of Starlette, for what the call
    bears, to the reply, its message.
    """

    method: "MethodDescriptor"
    handler: "Callable[[t.Any, Request], Awaitable[Message]]"


class BaseStarletteProtobufEndpoint(StarletteEndpoint):
    """
    The endpoint of the methods of services of protobuf over HTTP, of JSON,
    as their contract tells: the routes of the annotations
    ``google.api.http`` of its methods, :meth:`_iter_rpcs`, each to its
    handler; the request the canonical JSON of its message, of proto3, the
    fields of its names, the body ``*`` of the rule, the variables of its
    path and the query the rest; the reply the same, its fields of no
    presence given too, :attr:`IS_PRINTING_DEFAULTS`. A request not of its
    message, a field unknown, a value of another type, is refused by 400::

        class EchoEndpoint(BaseStarletteProtobufEndpoint):
            @t.override
            def _iter_rpcs(self):
                yield StarletteProtobufRpc(method=SEND_ECHO, handler=self.send)

            async def send(self, message, request):
                return echo_pb2.SendEchoResponse(text=message.text)

    An exception of a handler goes on to the policies of its subtree. Only a
    method of one request and one reply is transcoded, of a rule of a
    variable a field, a body ``*`` or none: the routes are built of what is
    taken, or refused by a ``TypeError``.
    """

    IS_PRINTING_DEFAULTS: t.ClassVar[bool] = True

    @t.final
    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        for rpc in self._iter_rpcs():
            method = rpc.method
            rule = get_http_rule(method)
            if rule is None:
                raise TypeError(f"{method.full_name}: no option google.api.http")
            if method.client_streaming or method.server_streaming:
                raise TypeError(f"{method.full_name}: no transcoding of a stream")
            yield Route(
                rule.path,
                self._create_endpoint(rpc, rule),
                methods=[rule.verb],
                name=method.name,
            )

    @abc.abstractmethod
    def _iter_rpcs(self) -> "Iterator[StarletteProtobufRpc]":
        """The methods transcoded and their handlers."""
        raise NotImplementedError

    @t.final
    def _create_endpoint(
        self, rpc: StarletteProtobufRpc, rule: HttpRule
    ) -> "Callable[[Request], Awaitable[Response]]":
        request_class = message_factory.GetMessageClass(rpc.method.input_type)

        async def endpoint(request: "Request") -> "Response":
            message = request_class()
            name = message.DESCRIPTOR.name
            if rule.body == "*":
                try:
                    data = json.loads(await request.body() or b"{}")
                except ValueError as error:
                    raise HTTPException(400, f"not a {name}: {error}") from None
                if not isinstance(data, dict):
                    raise HTTPException(400, f"not a {name}: not an object")
            else:
                data = _read_query(
                    request, rule, t.cast("Descriptor", message.DESCRIPTOR)
                )
            try:
                json_format.ParseDict(data, message)
                json_format.ParseDict(dict(request.path_params), message)
            except json_format.ParseError as error:
                raise HTTPException(400, f"not a {name}: {error}") from None
            reply = await rpc.handler(message, request)
            return JSONResponse(
                json_format.MessageToDict(
                    reply,
                    preserving_proto_field_name=True,
                    always_print_fields_with_no_presence=self.IS_PRINTING_DEFAULTS,
                )
            )

        return endpoint


def _read_query(
    request: "Request", rule: HttpRule, descriptor: "Descriptor"
) -> dict[str, t.Any]:
    # a field repeated is given again, a=1&a=2; the variables of the path win;
    # a bool of JSON a literal, of the query a string: true or false
    query: dict[str, t.Any] = {}
    for key in request.query_params:
        if key in rule.variables:
            continue
        field = descriptor.fields_by_name.get(key)
        is_bool = field is not None and field.type == FieldDescriptor.TYPE_BOOL
        values: list[t.Any] = [
            _BOOLS.get(value, value) if is_bool else value
            for value in request.query_params.getlist(key)
        ]
        query[key] = values if len(values) > 1 else values[0]
    return query


_BOOLS: t.Final = {"true": True, "false": False}
