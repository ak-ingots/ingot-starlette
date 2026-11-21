"""The rules of HTTP of the methods: the annotations google.api.http (AIP-127)."""

__all__ = ("HttpRule", "get_http_rule")

import re
import typing as t
from dataclasses import dataclass

from google.api import annotations_pb2

if t.TYPE_CHECKING:
    from google.api import http_pb2
    from google.protobuf.descriptor import MethodDescriptor
    from google.protobuf.descriptor_pb2 import MethodOptions
    from google.protobuf.internal.extension_dict import _ExtensionFieldDescriptor

    type _HttpExtension = _ExtensionFieldDescriptor[MethodOptions, http_pb2.HttpRule]

_VARIABLE: t.Final = re.compile(r"\{([^}]*)\}")
_FIELD: t.Final = re.compile(r"[a-z_][a-z0-9_]*")


@dataclass(frozen=True, slots=True, kw_only=True)
class HttpRule:
    """
    The rule of HTTP of a method: its :attr:`verb` of HTTP, its :attr:`path`,
    a template of Starlette, its :attr:`variables`, the fields of the request
    the path tells, and its :attr:`body`, ``"*"`` the whole request, ``""``
    none, the rest of the fields of the query.
    """

    verb: str
    path: str
    variables: tuple[str, ...]
    body: str


def get_http_rule(method: "MethodDescriptor") -> HttpRule | None:
    """
    The rule of HTTP of a method, of its option ``google.api.http``, or
    ``None`` without one. What the transcoding takes, checked when the routes
    are built, not at a request: a verb of the five; a variable a field of
    the request at the top, ``{text}``, no template of segments,
    ``{name=shelves/*}``, nor a field of a field, ``{book.name}``; a body
    ``"*"`` or none, not a field of the request.

    :raises TypeError: the rule takes what the transcoding does not.
    """
    # the stubs of googleapis-common-protos type the extension a plain field
    extension = t.cast("_HttpExtension", annotations_pb2.http)
    options = method.GetOptions()
    if not options.HasExtension(extension):
        return None
    rule = options.Extensions[extension]
    match rule.WhichOneof("pattern"):
        case "get":
            verb, template = "GET", rule.get
        case "put":
            verb, template = "PUT", rule.put
        case "post":
            verb, template = "POST", rule.post
        case "delete":
            verb, template = "DELETE", rule.delete
        case "patch":
            verb, template = "PATCH", rule.patch
        case pattern:
            raise TypeError(f"{method.full_name}: no transcoding of {pattern}")
    variables = tuple(_VARIABLE.findall(template))
    for variable in variables:
        if not _FIELD.fullmatch(variable):
            raise TypeError(f"{method.full_name}: no transcoding of {{{variable}}}")
    if rule.body not in ("", "*"):
        raise TypeError(f"{method.full_name}: no transcoding of the body {rule.body}")
    if rule.additional_bindings:
        raise TypeError(f"{method.full_name}: no transcoding of more bindings")
    return HttpRule(verb=verb, path=template, variables=variables, body=rule.body)
