"""The commands of the project: ``python . settings list``, from its root."""

import sys

from ingots.defaults.logging import configure_startup_logging
from ingots.puer.cli import CommandRunner

from project import EchoProject

configure_startup_logging()
sys.exit(CommandRunner(EchoProject).run())
