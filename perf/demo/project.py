"""
What the scenarios of the load of the demo share: the project of the
client with the configs of a run, ``PerfConfigs`` of ingots joined to its
own, and its clients of HTTP, components holding an ``httpx.AsyncClient``:
``default`` of the application on ``DEMO_PORT``, ``raw`` of the floor of
the stand, Starlette alone, on ``DEMO_RAW_PORT``.
"""

import abc
import logging
import typing as t

import httpx
from ingots.defaults import Project
from ingots.defaults.settings import SettingsUnit
from ingots.defaults.settings.configs import IntConfig, StrConfig
from ingots.perf import PerfConfigs
from ingots.puer import Component, Slot, Unit

logger = logging.getLogger(__name__)


class DemoPerfConfigs(PerfConfigs):
    DEMO_HOST = StrConfig("127.0.0.1")
    DEMO_PORT = IntConfig(8071)  # the application
    DEMO_RAW_PORT = IntConfig(8072)  # its floor, Starlette alone


class DemoPerfSettingsUnit(SettingsUnit):
    configs = Slot(DemoPerfConfigs)


class BaseDemoHttpClient(Component):
    """A client of HTTP of a server of the stand, its pool of connections."""

    SHUTDOWN_ORDER = 8

    project: "DemoPerfProject"

    _client: httpx.AsyncClient

    @t.final
    @property
    def client(self) -> httpx.AsyncClient:
        """The client of httpx, once configured."""
        return self._client

    @t.override
    async def _configure(self) -> None:
        configs = self.project.settings.configs
        base_url = f"http://{configs.DEMO_HOST}:{self._get_port()}"
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    @t.override
    async def _shut_down(self) -> None:
        await self._client.aclose()

    @abc.abstractmethod
    def _get_port(self) -> int:
        raise NotImplementedError


class DefaultDemoHttpClient(BaseDemoHttpClient):
    @t.override
    def _get_port(self) -> int:
        return self.project.settings.configs.DEMO_PORT


class RawDemoHttpClient(BaseDemoHttpClient):
    @t.override
    def _get_port(self) -> int:
        return self.project.settings.configs.DEMO_RAW_PORT


class DemoHttpUnit(Unit):
    default = Slot(DefaultDemoHttpClient)
    raw = Slot(RawDemoHttpClient)


class DemoPerfProject(Project):
    """The project of a scenario, which adds its unit ``perf``."""

    env_configs_prefix = "DEMO_TEST"
    settings = Slot(DemoPerfSettingsUnit)
    http = Slot(DemoHttpUnit)


class UnexpectedStatusError(Exception):
    """A response of another status than the scenario expects."""

    @classmethod
    def for_response(cls, response: httpx.Response, expected: int) -> t.Self:
        return cls(
            f"{response.request.url.path}: {response.status_code}, not {expected}",
            response.status_code,
        )


def check_status(response: httpx.Response, expected: int) -> None:
    """Raises :class:`UnexpectedStatusError` unless the status is ``expected``."""
    if response.status_code != expected:
        raise UnexpectedStatusError.for_response(response, expected)


# the text of every echo: its size is not under test
TEXT: t.Final = "hello"
BODY: t.Final = {"text": TEXT}
