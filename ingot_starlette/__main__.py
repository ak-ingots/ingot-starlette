"""Runs the addon on its own: ``python -m ingot_starlette logging info``."""

import sys

from ingots.defaults.logging import configure_startup_logging
from ingots.defaults.cli import CommandRunner

from .project import StarletteProject


def main() -> None:
    configure_startup_logging()
    sys.exit(CommandRunner(StarletteProject).run())


if __name__ == "__main__":
    main()
