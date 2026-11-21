"""
The project of the echo over Starlette, of the units of its parts: the
domain, ``echo``, of no transport; ``extensions``, what it extends of the
framework and of the addon, the settings, the logging, the operations and
Starlette, its endpoints, of the API and of the pages. As the echo of
ingot-grpcio, to compare them.

=========================  ==================================================
``POST /api/echo``         ``{"text": ...}`` -> ``{"text": ...}``
``GET /api/echo/{text}``   ``{"text": ...}``
``POST /api/fail``         ``{"text": ...}`` -> 409, its problem
``GET /api/ticks``         ``?count=&interval=&fail_at=``, NDJSON
``WS /ws/stream``          ``{"text": ...}`` echoed; ``fail`` closes it, 4409
``WS /ws/chat``            echoes and ticks beside, a problem the WS kept
``GET /``                  a page of HTML, a form of the echo
``POST /echo``, ``/fail``  the form posted: a redirect, 303, or a page of 409
``GET /socket``            a page whose script opens ``/ws/stream``
``GET /version``           a function of Starlette, in ``asgi.py``
``GET /health/``           ``ok``, a router of Starlette, in ``asgi.py``
=========================  ==================================================
"""

__all__ = ("EchoProject",)

from ingots.puer import Slot

from ingot_starlette import StarletteProject

from echo import EchoUnit
from extensions.logging import EchoLoggingUnit
from extensions.operations import EchoOperationsUnit
from extensions.settings import EchoSettingsUnit
from extensions.starlette import EchoStarletteUnit


class EchoProject(StarletteProject):
    env_configs_prefix = "APP"
    settings = Slot(EchoSettingsUnit)
    logging = Slot(EchoLoggingUnit)
    operations = Slot(EchoOperationsUnit)
    starlette = Slot(EchoStarletteUnit)
    echo = Slot(EchoUnit)
