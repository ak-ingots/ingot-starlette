`examples/demo` is laid out as an application is: at its root `project.py`,
collecting `extensions/`, a module each for what it extends, the settings,
the logging, the operations and Starlette, beside the domain `echo/`, run
as `uvicorn asgi:app` from it, its Docker files beside it.
