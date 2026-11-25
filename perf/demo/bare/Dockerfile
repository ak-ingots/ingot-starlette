# The floor of the demo: its routes on Starlette alone, at the versions of
# the demo of the role.
ARG PYTHON
FROM python:${PYTHON}-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
COPY dist/demo-requirements.txt /dist/
RUN uv pip install --system --no-cache -r /dist/demo-requirements.txt
WORKDIR /srv
COPY --from=stand bare/ bare/
ENTRYPOINT ["uvicorn"]
CMD ["bare:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
