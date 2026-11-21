"""The transcoding of the services of protobuf to HTTP, of JSON."""

import typing as t
import unittest

from google.api import annotations_pb2, http_pb2
from google.protobuf import descriptor_pb2, descriptor_pool
from google.rpc import code_pb2
from ingots.puer import Slot
from starlette.requests import Request
from starlette.testclient import TestClient

from ingot_starlette import StarletteProject
from ingot_starlette.contrib.protobuf import (
    BaseStarletteProtobufEndpoint,
    StarletteProtobufRpc,
    get_http_rule,
    get_http_status,
)
from ingot_starlette.runner import StarletteRunner
from ingot_starlette.starlette import StarletteApiUnit, StarletteUnit
from ingot_starlette.starlette.errors import (
    BaseStaticStarletteErrorPolicy,
    StarletteErrorsUnit,
)

from .proto import echo_pb2

if t.TYPE_CHECKING:
    from collections.abc import Iterator

ECHO: t.Final = echo_pb2.DESCRIPTOR.services_by_name["Echo"]


class EchoFailedError(Exception):
    pass


class EchoFailedPolicy(BaseStaticStarletteErrorPolicy):
    EXCEPTION = EchoFailedError
    STATUS = get_http_status(code_pb2.FAILED_PRECONDITION)
    TYPE = "https://echo.example.com/problems/echo-failed"


class EchoEndpoint(BaseStarletteProtobufEndpoint):
    async def send(
        self, message: echo_pb2.SendEchoRequest, request: Request
    ) -> echo_pb2.SendEchoResponse:
        reply = echo_pb2.SendEchoResponse(text=message.text, times=message.times * 2)
        if message.HasField("at"):
            reply.at.CopyFrom(message.at)
        return reply

    async def get(
        self, message: echo_pb2.GetEchoRequest, request: Request
    ) -> echo_pb2.SendEchoResponse:
        text = message.text.upper() if message.loud else message.text
        return echo_pb2.SendEchoResponse(text=text)

    async def list(
        self, message: echo_pb2.ListEchoesRequest, request: Request
    ) -> echo_pb2.ListEchoesResponse:
        texts = [f"{message.filter}{index}" for index in range(message.page_size)]
        return echo_pb2.ListEchoesResponse(texts=texts)

    async def fail(
        self, message: echo_pb2.SendEchoRequest, request: Request
    ) -> echo_pb2.SendEchoResponse:
        raise EchoFailedError(f"the echo of {message.text!r} failed")

    @t.override
    def _iter_rpcs(self) -> "Iterator[StarletteProtobufRpc]":
        methods = ECHO.methods_by_name
        yield StarletteProtobufRpc(method=methods["SendEcho"], handler=self.send)
        yield StarletteProtobufRpc(method=methods["GetEcho"], handler=self.get)
        yield StarletteProtobufRpc(method=methods["ListEchoes"], handler=self.list)
        yield StarletteProtobufRpc(method=methods["FailEcho"], handler=self.fail)


class EchoApiUnit(StarletteApiUnit):
    echo = Slot(EchoEndpoint)

    @t.override
    def _iter_routes(self) -> "Iterator[t.Any]":
        yield from self.echo.get_routes()


class EchoErrorsUnit(StarletteErrorsUnit):
    echo_failed = Slot(EchoFailedPolicy)


class EchoStarletteUnit(StarletteUnit):
    errors = Slot(EchoErrorsUnit)
    api = Slot(EchoApiUnit)


class EchoProject(StarletteProject):
    starlette = Slot(EchoStarletteUnit)


class TranscodingTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.client = self.enterContext(TestClient(StarletteRunner(EchoProject)))

    def test_the_body_is_the_request(self) -> None:
        response = self.client.post(
            "/api/v1/echoes:send",
            json={"text": "hi", "times": "21", "at": "2026-11-21T10:00:00Z"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"text": "hi", "times": "42", "at": "2026-11-21T10:00:00Z"},
        )

    def test_the_fields_of_no_presence_are_given(self) -> None:
        response = self.client.post("/api/v1/echoes:send", json={})
        self.assertEqual(response.json(), {"text": "", "times": "0"})

    def test_a_variable_of_the_path_and_the_query(self) -> None:
        response = self.client.get("/api/v1/echoes/hi", params={"loud": "true"})
        self.assertEqual(response.json(), {"text": "HI", "times": "0"})
        response = self.client.get("/api/v1/echoes/hi", params={"text": "other"})
        self.assertEqual(response.json()["text"], "hi")  # the path wins

    def test_the_query_alone(self) -> None:
        response = self.client.get(
            "/api/v1/echoes", params={"page_size": "3", "filter": "e"}
        )
        self.assertEqual(response.json(), {"texts": ["e0", "e1", "e2"]})

    def test_a_request_not_of_its_message_is_bad(self) -> None:
        for body in (b"not json", b'{"nope": 1}', b'{"times": "many"}', b"[]"):
            with self.subTest(body=body):
                response = self.client.post(
                    "/api/v1/echoes:send",
                    content=body,
                    headers={"content-type": "application/json"},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.headers["content-type"], "application/problem+json"
                )
        response = self.client.get("/api/v1/echoes", params={"page_size": "x"})
        self.assertEqual(response.status_code, 400)

    def test_a_failure_answers_by_its_policy(self) -> None:
        response = self.client.post("/api/v1/echoes:fail", json={"text": "hi"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["type"], "https://echo.example.com/problems/echo-failed"
        )

    def test_a_method_of_no_rule_is_not_served(self) -> None:
        self.assertEqual(self.client.post("/api/v1/echoes:hide").status_code, 404)

    def test_a_repeated_field_of_the_query(self) -> None:
        response = self.client.get("/api/v1/echoes", params={"page_size": "1"})
        self.assertEqual(response.json(), {"texts": ["0"]})


class StatusesTestCase(unittest.TestCase):
    def test_the_statuses_of_aip_193(self) -> None:
        for code, status in (
            (code_pb2.OK, 200),
            (code_pb2.INVALID_ARGUMENT, 400),
            (code_pb2.UNAUTHENTICATED, 401),
            (code_pb2.PERMISSION_DENIED, 403),
            (code_pb2.NOT_FOUND, 404),
            (code_pb2.ALREADY_EXISTS, 409),
            (code_pb2.RESOURCE_EXHAUSTED, 429),
            (code_pb2.UNAVAILABLE, 503),
            (99, 500),
        ):
            with self.subTest(code=code):
                self.assertEqual(get_http_status(code), status)


def make_method(rule: http_pb2.HttpRule | None, *, streaming: bool = False) -> t.Any:
    """A method of a service of a file of its own, of a rule given."""
    package = f"rules{len(_FILES)}"
    _FILES.append(package)
    file = descriptor_pb2.FileDescriptorProto(
        name=f"{package}.proto",
        package=package,
        dependency=["google/api/annotations.proto"],
    )
    file.message_type.add(name="Message")
    method = file.service.add(name="Service").method.add(
        name="Call",
        input_type=f".{package}.Message",
        output_type=f".{package}.Message",
        server_streaming=streaming,
    )
    if rule is not None:
        method.options.Extensions[t.cast(t.Any, annotations_pb2.http)].CopyFrom(rule)
    pool = descriptor_pool.Default()
    pool.AddSerializedFile(file.SerializeToString())
    return pool.FindMethodByName(f"{package}.Service.Call")


_FILES: list[str] = []


class RulesTestCase(unittest.TestCase):
    def test_the_verbs(self) -> None:
        path = "/v1/things/{name}"
        for rule, verb in (
            (http_pb2.HttpRule(get=path), "GET"),
            (http_pb2.HttpRule(put=path), "PUT"),
            (http_pb2.HttpRule(post=path), "POST"),
            (http_pb2.HttpRule(delete=path), "DELETE"),
            (http_pb2.HttpRule(patch=path), "PATCH"),
        ):
            with self.subTest(verb=verb):
                parsed = get_http_rule(make_method(rule))
                assert parsed is not None
                self.assertEqual(
                    (parsed.verb, parsed.path, parsed.variables),
                    (verb, path, ("name",)),
                )

    def test_what_is_not_transcoded_is_refused(self) -> None:
        custom = http_pb2.HttpRule(
            custom=http_pb2.CustomHttpPattern(kind="HEAD", path="/v1/x")
        )
        segments = http_pb2.HttpRule(get="/v1/{name=shelves/*}")
        nested = http_pb2.HttpRule(get="/v1/{book.name}")
        field_body = http_pb2.HttpRule(post="/v1/x", body="book")
        more = http_pb2.HttpRule(
            get="/v1/x", additional_bindings=[http_pb2.HttpRule(get="/v2/x")]
        )
        for rule in (custom, segments, nested, field_body, more):
            with self.subTest(rule=str(rule)):
                with self.assertRaises(TypeError):
                    get_http_rule(make_method(rule))
        self.assertIsNone(get_http_rule(make_method(None)))

    def test_a_stream_or_no_rule_fails_the_start(self) -> None:
        stream = make_method(http_pb2.HttpRule(get="/v1/x"), streaming=True)
        for method in (stream, make_method(None)):
            with self.subTest(method=method.full_name):
                RefusedEndpoint.METHOD = method
                runner = StarletteRunner(RefusedProject)
                with self.assertRaisesRegex(TypeError, method.full_name):
                    with TestClient(runner):
                        pass  # pragma: no cover


class RefusedEndpoint(BaseStarletteProtobufEndpoint):
    """Of a method the test tells, which the transcoding refuses."""

    METHOD: t.ClassVar[t.Any]

    async def call(self, message: t.Any, request: Request) -> t.Any:
        raise AssertionError("never: refused")  # pragma: no cover

    @t.override
    def _iter_rpcs(self) -> "Iterator[StarletteProtobufRpc]":
        yield StarletteProtobufRpc(method=self.METHOD, handler=self.call)


class RefusedApiUnit(StarletteApiUnit):
    refused = Slot(RefusedEndpoint)

    @t.override
    def _iter_routes(self) -> "Iterator[t.Any]":
        yield from self.refused.get_routes()


class RefusedStarletteUnit(StarletteUnit):
    api = Slot(RefusedApiUnit)


class RefusedProject(StarletteProject):
    starlette = Slot(RefusedStarletteUnit)
