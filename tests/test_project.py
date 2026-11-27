import contextlib
import io
import os
import typing as t
import unittest
from unittest import mock

import ingot_starlette
from ingot_starlette.__main__ import main
from ingot_starlette.logging import StarletteLoggingUnit
from ingot_starlette.settings import StarletteSettingsUnit
from ingot_starlette.settings.configs import StarletteConfigs
from ingot_starlette.starlette import StarletteUnit
from ingots.defaults import Project
from ingots.defaults.cli import CommandRunner


class ProjectTestCase(unittest.TestCase):
    @t.override
    def setUp(self) -> None:
        self.enterContext(mock.patch.dict(os.environ, clear=True))
        # the logging is not under test: keep the handlers of the test run
        self.enterContext(mock.patch("logging.config.dictConfig"))

    def run_project(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = CommandRunner(
                ingot_starlette.StarletteProject,
                ["--config", "IS_PRINT_CONFIGS=off", *argv],
            ).run()
        return code, out.getvalue()

    def test_the_project_extends_the_defaults(self) -> None:
        self.assertTrue(issubclass(ingot_starlette.StarletteProject, Project))
        self.assertIs(
            ingot_starlette.StarletteProject.settings.cls, StarletteSettingsUnit
        )
        self.assertIs(
            ingot_starlette.StarletteProject.logging.cls, StarletteLoggingUnit
        )
        self.assertIs(ingot_starlette.StarletteProject.starlette.cls, StarletteUnit)
        self.assertIs(StarletteSettingsUnit.configs.cls, StarletteConfigs)

    def test_the_configs_of_the_addon_are_read(self) -> None:
        os.environ["INGOT_STARLETTE_LOGGING_LEVEL"] = "debug"
        code, out = self.run_project("settings", "list")
        self.assertEqual(code, 0)
        self.assertIn("STARLETTE_LOGGING_LEVEL = DEBUG\n", out)

    def test_the_logging_has_the_logger_of_the_addon(self) -> None:
        code, out = self.run_project(
            "--config", "STARLETTE_LOGGING_LEVEL=warning", "logging", "info"
        )
        self.assertEqual(code, 0)
        self.assertIn("        ingot_starlette:\n            level: 30\n", out)

    def test_the_addon_runs_on_its_own(self) -> None:
        os.environ["INGOT_IS_PRINT_CONFIGS"] = "off"
        with (
            mock.patch("sys.argv", ["ingot_starlette", "logging", "info"]),
            contextlib.redirect_stdout(io.StringIO()) as out,
            self.assertRaises(SystemExit) as exit,
        ):
            main()
        self.assertEqual(exit.exception.code, 0)
        self.assertIn("ingot_starlette:", out.getvalue())
