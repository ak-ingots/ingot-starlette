# The demo, as an application is installed: the wheel of ingot-starlette that
# `make all` builds, with its dependencies and its server, uvicorn, at the
# versions of uv.lock, which `make perf-build` exports next to it; then the
# code of the example. Built from the root of the repository, on the Python
# of DEMO_PYTHON: the stand's for a run, the newest of PYTHONS for
# `make perf-smoke`.
ARG PYTHON
FROM python:${PYTHON}-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
COPY dist/ /dist/
RUN uv pip install --system --no-cache -r /dist/demo-requirements.txt \
    "$(ls /dist/*.whl)"
WORKDIR /srv
COPY examples/demo/ demo/
ENTRYPOINT ["uvicorn"]
CMD ["demo.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
