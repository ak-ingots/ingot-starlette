"""
The endpoint of the ticks, a stream over HTTP, NDJSON: the status of the
response goes with its first item, so the first item is read before it,
a failure before it the response, its problem; after it, an item, the last.
"""

__all__ = ("TicksEndpoint",)

import json
import typing as t

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from starlette.routing import Route

from ingot_starlette.starlette import StarletteEndpoint
from ingot_starlette.starlette.errors import encode_problem

from echo.operations import TicksParameters

if t.TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator

    from starlette.routing import BaseRoute

    from project import EchoProject
    from ingot_starlette.operations import OperationStream

NDJSON: t.Final = "application/x-ndjson"


class TicksEndpoint(StarletteEndpoint):
    """``GET /ticks?count=&interval=&fail_at=``, a line ``{"tick": n}`` each."""

    project: "EchoProject"

    async def watch(self, request: Request) -> Response:
        parameters = TicksParameters(
            count=int(request.query_params.get("count", 0)),
            interval=float(request.query_params.get("interval", 0.1)),
            fail_at=int(request.query_params.get("fail_at", 0)),
        )
        stream = await self.project.starlette.run_operation(
            self.project.echo.op_ticks, parameters, request
        )
        try:
            first = await anext(stream)
        except StopAsyncIteration:
            await stream.aclose()
            return Response(media_type=NDJSON)
        except Exception:
            await stream.aclose()
            raise
        lines = self._encode(first, stream, request)
        return StreamingResponse(lines, media_type=NDJSON)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield Route("/ticks", self.watch)

    async def _encode(
        self, first: int, stream: "OperationStream[int]", request: Request
    ) -> "AsyncIterator[bytes]":
        async with stream:
            yield _encode_line({"tick": first})
            try:
                async for tick in stream:
                    yield _encode_line({"tick": tick})
            except Exception as error:
                problem = self.project.starlette.errors.encode(error, request)
                yield _encode_line({"problem": encode_problem(problem)})


def _encode_line(item: object) -> bytes:
    return json.dumps(item).encode() + b"\n"
