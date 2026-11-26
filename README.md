# ingot-starlette

[![PyPI](https://img.shields.io/pypi/v/ingot-starlette.svg)](https://pypi.org/project/ingot-starlette/)
[![Python](https://img.shields.io/pypi/pyversions/ingot-starlette.svg)](https://pypi.org/project/ingot-starlette/)
[![ci](https://github.com/ak-ingots/ingot-starlette/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ak-ingots/ingot-starlette/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/ak-ingots/ingot-starlette/blob/main/LICENSE)

<!-- Links must be absolute: this README also renders on PyPI. -->

Integration of Starlette, the ASGI framework, into Ingots applications. An
addon of [Ingots](https://github.com/ak-ingots/ingots).

**Status:** pre-alpha: the skeleton of the addon, its project, settings and
logging; the application of Starlette comes next, on ingot-asgi.

## For Consumers

### Install

```sh
uv add ingot-starlette
```

### Integrate

An application of Ingots has its own configs, settings, logging and project;
each takes the class of the addon among its bases:

```python
# app/project.py
import typing as t

from ingot_starlette import StarletteProject
from ingot_starlette.logging import StarletteLoggingUnit
from ingot_starlette.settings import StarletteSettingsUnit
from ingot_starlette.settings.configs import StarletteConfigs
from ingots.puer import Slot


class AppConfigs(StarletteConfigs):
    pass


class AppSettingsUnit(StarletteSettingsUnit):
    configs = Slot(AppConfigs)


class AppLoggingUnit(StarletteLoggingUnit):
    project: "AppProject"


class AppProject(StarletteProject):
    env_configs_prefix = "APP"
    settings = Slot(AppSettingsUnit)
    logging = Slot(AppLoggingUnit)
```

With other addons, their classes join the same bases:
`class AppConfigs(RedisConfigs, StarletteConfigs)`, and so on, as the
[addon guide](https://github.com/ak-ingots/ingots/blob/main/docs/defaults/addon.md)
of Ingots shows. An application with this addon alone may inherit
`StarletteProject` and nothing more.

The application runs through its own `__main__.py`:

```python
# app/__main__.py
import sys

from ingots.defaults.logging import configure_startup_logging
from ingots.defaults.cli import CommandRunner

from .project import AppProject

configure_startup_logging()
sys.exit(CommandRunner(AppProject).run())
```

```sh
uv run python -m app settings list  # the configs, STARLETTE_* among them
uv run python -m app logging info   # the loggers, ingot_starlette among them
```

### Configs

Set as environment variables with the prefix of the project
(`APP_STARLETTE_LOGGING_LEVEL`), in a `--configs-file` or with `--config`.

| Name | Default | Meaning |
|---|---|---|
| `STARLETTE_LOGGING_LEVEL` | `INFO` | the level of the logger of the addon, `ingot_starlette` |
| `STARLETTE_IS_DEBUG` | `False` | whether a failed request answers with its traceback; never in production |

## Development

Requires [uv](https://docs.astral.sh/uv/) and `make`; uv fetches the
interpreters it needs.

```sh
make                 # the target list
make check           # everything CI runs: lint, test, coverage, wheel-test, cl-check
make format          # black
make all             # build the sdist and the wheel into dist/
make perf-smoke      # the scenarios of the load, dry, against the demo in Docker
```

- Every change users should know about adds a news fragment to `changelog.d/`
  (see [its README](https://github.com/ak-ingots/ingot-starlette/blob/main/changelog.d/README.md)).
- A release is a pull request setting the version (`uv version X.Y.Z`) and
  collating the changelog (`make cl-build VERSION=X.Y.Z`), then the tag
  `vX.Y.Z` on `main`: the `release` workflow publishes the tested build to
  TestPyPI, tests it as installed from there, then
  publishes it to PyPI. Run by hand, it rehearses on TestPyPI only.
