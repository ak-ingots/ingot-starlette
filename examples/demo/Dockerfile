# PYTHON: the stand's for a run, the newest of PYTHONS for `make perf-smoke`.
ARG PYTHON
FROM python:${PYTHON}-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
COPY dist/ /dist/
RUN uv pip install --system --no-cache -r /dist/demo-requirements.txt \
    "$(ls /dist/*.whl)"
WORKDIR /srv
COPY examples/demo/ ./
ENTRYPOINT ["uvicorn"]
CMD ["asgi:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
