# ingot-starlette Changelog

<!-- towncrier release notes start -->

## [0.3.1] - 2026-11-21
### Fixed
- `StarletteEndpoint` takes any project, `Project` of the defaults, not
  `StarletteProject` alone, so that an endpoint mixing in the RPCs of an
  addon takes the project of the addon.

## [0.3.0] - 2026-11-21
### Added
- Added the transcoding of the services of protobuf to HTTP, by the extra
  `protobuf` (protobuf and googleapis-common-protos, no grpcio):
  `BaseStarletteProtobufEndpoint` routes each method of
  `StarletteProtobufRpc` its addon gives by the annotation `google.api.http`
  of its contract (AIP-127), the request and the reply the canonical JSON of
  proto3 of their messages, the body `*`, the variables of the path and the
  query; a request not of its message is refused by 400, a rule it does not
  transcode, a stream or a method of no rule fail the start. `get_http_status`
  gives the status of HTTP of a code of `google.rpc` (AIP-193).

## [0.2.0] - 2026-11-21
### Added
- Added the subtree of the WebSockets, `ws` of `StarletteUnit`, a
  `StarletteWebSocketsUnit` at `/ws`: a resource of a state of its own for
  each connection, `BaseStarletteWebSocketResource`, by a factory and a
  `StarletteWebSocketRoute`; its caller told once, at the handshake, its
  operations run for it; `_open` may refuse it before the accept, each
  message of JSON goes to `_receive`, a failure closes it by `4000 + status`,
  `send_problem` tells one keeping it, a shutdown closes it by 1001. A
  request of HTTP is refused by 426, a WebSocket of another origin than the
  `Host` by 403 unless `_iter_origins` allows it. The API refuses a
  WebSocket by 404.

### Changed
- `StarletteUnit` mounts subtrees of its own, each a mount of its own
  middleware and errors, `ws` of the WebSockets beside: `api`, a `StarletteApiUnit` at `/api`, of JSON alone,
  refusing an `Accept` of no JSON by 406 and a body not of JSON by 415, its
  errors problems of `application/problem+json`; `pages`, a
  `StarlettePagesUnit` at the root, of HTML, its errors pages of HTML. The
  error policies are shared and tell the problem; a renderer of each subtree,
  `StarletteJsonProblemRenderer` or `StarletteHtmlProblemRenderer`, its form.
  Its own routes are those of the subtrees; the handlers given by
  `add_exception_handler` answer outside them.

## [0.1.0] - 2026-11-21
### Added
- Started ingot-starlette, an addon of Ingots for Starlette, for `ingots`
  0.36. `StarletteProject` takes the addon's `StarletteSettingsUnit`, whose
  `StarletteConfigs` add `STARLETTE_LOGGING_LEVEL`, `StarletteLoggingUnit`,
  which adds the logger `ingot_starlette`, and `StarletteUnit`.
  `python -m ingot_starlette` runs it on its own.
- Added `StarletteRunner`, the application of Starlette an ASGI server
  imports with the project inside: the lifespan configures the project and
  shuts it down, and the configured project gives the application its routes,
  middleware and exception handlers through `StarletteUnit`, the root endpoint.
  Endpoints are the entities of `StarletteEndpoint` in slots, each with the
  routes to its methods; one that is a unit too mounts those of its own, a
  tree. Operations run for the caller `StarletteCallers` tells, anonymous by
  default, by `StarletteUnit.run_operation`. Exceptions answer by the policies of
  `StarletteErrorsUnit`, problems of RFC 9457, handled by Starlette's
  exception handlers, `HTTPException` and internal faults among them. What
  the application is given the Starlette way before its first startup stays
  beside the project's: `add_route` and `mount` routes, `add_middleware`,
  `add_exception_handler` over the policies, `debug`. `STARLETTE_IS_DEBUG`
  turns on Starlette's debug mode too. `BaseStreamOperation`
  of `ingot_starlette.operations` is an operation giving a stream, read in
  the log context of its run, a draft for `ingots`.
