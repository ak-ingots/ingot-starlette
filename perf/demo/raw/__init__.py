"""
``uvicorn raw:app``: the routes of the echo of the demo on Starlette alone,
no project, no operation, no policy, as the floor of its cost: the same
bodies, the same problem of a failure, a constant.
"""

import json

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

PROBLEM: bytes = json.dumps(
    {
        "type": "https://echo.example.com/problems/echo-failed",
        "status": 409,
        "title": "The echo failed",
    }
).encode()


async def send(request: Request) -> Response:
    return JSONResponse({"text": (await request.json())["text"]})


async def fail(request: Request) -> Response:
    await request.json()
    return Response(PROBLEM, status_code=409, media_type="application/problem+json")


app = Starlette(
    routes=[
        Mount(
            "/api",
            routes=[
                Route("/echo", send, methods=["POST"]),
                Route("/fail", fail, methods=["POST"]),
            ],
        )
    ]
)
