Added `StarletteRunner`, the application of Starlette an ASGI server
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
