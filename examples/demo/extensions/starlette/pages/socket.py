"""
A page of the echo over a WebSocket: its script opens ``/ws/stream`` of the
same site, so its origin passes, and sends each line of its form,
``{"text": ...}``; the echoes, the problems and the close shown below.
``fail`` fails, closing it by 4409; ``Reconnect`` opens it again.
"""

__all__ = ("SocketPage",)

import typing as t

from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from ingot_starlette.starlette import StarletteEndpoint

if t.TYPE_CHECKING:
    from collections.abc import Iterator

    from starlette.routing import BaseRoute

PAGE: t.Final = """<!doctype html>
<html><head><title>Echo over a WebSocket</title>
<style>
body { font-family: sans-serif; max-width: 40rem; margin: 2rem auto; }
#log { border: 1px solid #ccc; padding: .5rem; height: 20rem; overflow-y: auto;
       font-family: monospace; white-space: pre-wrap; }
.in { color: #060; } .out { color: #036; }
.info { color: #888; } .error { color: #a00; }
</style></head>
<body>
<h1>Echo over a WebSocket</h1>
<p><a href="/">the form of HTTP</a> &middot; <span id="state">connecting</span></p>
<form id="form"><input id="text" autocomplete="off" autofocus>
<button>Send</button> <button type="button" id="reconnect">Reconnect</button></form>
<div id="log"></div>
<script>
const log = document.getElementById("log"), state = document.getElementById("state");
function show(kind, text) {
  const line = document.createElement("div");
  line.className = kind; line.textContent = text;
  log.appendChild(line); log.scrollTop = log.scrollHeight;
}
let socket;
function connect() {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${scheme}://${location.host}/ws/stream`);
  state.textContent = "connecting";
  socket.onopen = () => { state.textContent = "open"; show("info", "open"); };
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.problem) show("error", "problem: " + JSON.stringify(message.problem));
    else show("in", "< " + message.text);
  };
  socket.onclose = (event) => {
    state.textContent = "closed " + event.code;
    show("info", `closed: ${event.code} ${event.reason}`);
  };
}
document.getElementById("form").onsubmit = (event) => {
  event.preventDefault();
  const input = document.getElementById("text");
  if (socket.readyState !== WebSocket.OPEN) { show("error", "not open"); return; }
  socket.send(JSON.stringify({text: input.value}));
  show("out", "> " + input.value); input.value = "";
};
document.getElementById("reconnect").onclick = () => { socket.close(); connect(); };
connect();
</script>
</body></html>
"""


class SocketPage(StarletteEndpoint):
    """``GET /socket``: the page of the echo over a WebSocket."""

    async def show(self, request: Request) -> Response:
        return HTMLResponse(PAGE)

    @t.override
    def _iter_routes(self) -> "Iterator[BaseRoute]":
        yield Route("/socket", self.show, name="socket")
