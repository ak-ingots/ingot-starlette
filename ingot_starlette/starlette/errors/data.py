"""The data of the errors."""

__all__ = ("StarletteProblem",)

import typing as t
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, kw_only=True)
class StarletteProblem:
    """
    The problem details of RFC 9457 a failed request answers with, as
    ``application/problem+json``: :attr:`status` of HTTP, :attr:`type` a URI
    of the problem, ``about:blank`` for one the status tells, :attr:`title`
    the same for every problem of the type, :attr:`detail` of this one and
    :attr:`extensions` of the type, members of the body too; :attr:`headers`
    go with the response.
    """

    status: int
    type: str = "about:blank"
    title: str = ""
    detail: str | None = None
    extensions: t.Mapping[str, object] = field(default_factory=dict)
    headers: t.Mapping[str, str] = field(default_factory=dict)
