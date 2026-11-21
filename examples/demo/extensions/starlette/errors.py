"""The policies of the exceptions of the echo: the problems they answer with."""

__all__ = ("EchoFailedPolicy", "EchoStarletteErrorsUnit")

import typing as t

from ingots.puer import Slot

from ingot_starlette.starlette.errors import (
    BaseStaticStarletteErrorPolicy,
    StarletteErrorsUnit,
)

from echo.errors import EchoFailedError


class EchoFailedPolicy(BaseStaticStarletteErrorPolicy):
    EXCEPTION = EchoFailedError
    STATUS = 409
    TYPE = "https://echo.example.com/problems/echo-failed"
    TITLE = "The echo failed"

    @t.override
    def _get_extensions(self, error: Exception) -> t.Mapping[str, object]:
        return {"text": t.cast(EchoFailedError, error).text}


class EchoStarletteErrorsUnit(StarletteErrorsUnit):
    echo_failed = Slot(EchoFailedPolicy)
