"""The streams of examples/demo over HTTP: NDJSON."""

import json
import typing as t
import unittest

from demo.asgi import app
from starlette.testclient import TestClient


class HttpStreamTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.client = self.enterContext(TestClient(app))

    def get_lines(self, **params: object) -> tuple[int, list[t.Any]]:
        response = self.client.get("/api/ticks", params={"interval": 0, **params})
        return response.status_code, [
            json.loads(line) for line in response.text.splitlines()
        ]

    def test_the_items_are_lines(self) -> None:
        self.assertEqual(
            self.get_lines(count=3), (200, [{"tick": 1}, {"tick": 2}, {"tick": 3}])
        )

    def test_a_failure_after_the_status_is_the_last_line(self) -> None:
        status, lines = self.get_lines(count=5, fail_at=3)
        self.assertEqual(status, 200)
        self.assertEqual(lines[:2], [{"tick": 1}, {"tick": 2}])
        self.assertEqual(lines[2]["problem"]["status"], 409)
        self.assertEqual(len(lines), 3)

    def test_a_failure_before_the_first_item_is_the_response(self) -> None:
        response = self.client.get("/api/ticks", params={"interval": 0, "fail_at": 1})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["content-type"], "application/problem+json")

    def test_a_stream_of_no_item(self) -> None:
        self.assertEqual(self.get_lines(count=-1), (200, []))
