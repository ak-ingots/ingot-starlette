"""
The project of the echo over Starlette, of the units of its parts: the
domain, ``echo``, of no transport; ``starlette``, its endpoints. As the echo
of ingot-grpcio, to compare them.

========================  ==============================================
``POST /api/echo``        ``{"text": ...}`` -> ``{"text": ...}``
``GET /api/echo/{text}``  ``{"text": ...}``
``POST /api/fail``        ``{"text": ...}`` -> 409, its problem
``GET /api/ticks``        ``?count=&interval=&fail_at=``, NDJSON
``WS /api/stream``        each text echoed; ``fail`` closes it, 4409
``GET /version``          a function of Starlette, in ``asgi.py``
``GET /health/``          ``ok``, a router of Starlette, in ``asgi.py``
========================  ==============================================
"""

__all__ = ("EchoProject",)

from ingots.puer import Slot

from ingot_starlette import StarletteProject

from .echo import EchoUnit
from .operations import EchoOperationsUnit
from .starlette import EchoStarletteUnit


class EchoProject(StarletteProject):
    env_configs_prefix = "APP"
    operations = Slot(EchoOperationsUnit)
    starlette = Slot(EchoStarletteUnit)
    echo = Slot(EchoUnit)
