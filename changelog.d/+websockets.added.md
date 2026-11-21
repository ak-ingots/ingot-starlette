Added the subtree of the WebSockets, `ws` of `StarletteUnit`, a
`StarletteWebSocketsUnit` at `/ws`: a resource of a state of its own for
each connection, `BaseStarletteWebSocketResource`, by a factory and a
`StarletteWebSocketRoute`; its caller told once, at the handshake, its
operations run for it; `_open` may refuse it before the accept, each
message of JSON goes to `_receive`, a failure closes it by `4000 + status`,
`send_problem` tells one keeping it, a shutdown closes it by 1001. A
request of HTTP is refused by 426, a WebSocket of another origin than the
`Host` by 403 unless `_iter_origins` allows it. The API refuses a
WebSocket by 404.
