"""Test cases for the write_templates function."""

import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from pymake.write_templates import PATHS, TEMPLATES, podman_scaffold


class TestPodmanScaffold(unittest.TestCase):
    @patch("pymake.write_templates.create_paths")
    @patch("pymake.write_templates.write_templates")
    @patch("pymake.write_templates.Path.cwd")
    def test_podman_scaffold_default(self, mock_cwd, mock_write_templates, mock_create_paths):
        runner = CliRunner()
        result = runner.invoke(podman_scaffold, [])

        self.assertEqual(result.exit_code, 0)
        mock_cwd.assert_called_once()
        self.assertListEqual(list(mock_create_paths.call_args[0][0]), list(PATHS.values()))
        mock_write_templates.assert_called_once_with(TEMPLATES, False)

    @patch("pymake.write_templates.create_paths")
    @patch("pymake.write_templates.write_templates")
    @patch("pymake.write_templates.Path.cwd")
    def test_podman_scaffold_overwrite(self, mock_cwd, mock_write_templates, mock_create_paths):
        runner = CliRunner()
        result = runner.invoke(podman_scaffold, ["--overwrite"])

        self.assertEqual(result.exit_code, 0)
        mock_cwd.assert_called_once()
        self.assertListEqual(list(mock_create_paths.call_args[0][0]), list(PATHS.values()))
        mock_write_templates.assert_called_once_with(TEMPLATES, True)

    @patch("pymake.write_templates.create_paths")
    @patch("pymake.write_templates.write_templates")
    @patch("pymake.write_templates.Path.cwd")
    def test_podman_scaffold_create_paths_called(self, mock_cwd, mock_write_templates, mock_create_paths):
        runner = CliRunner()
        runner.invoke(podman_scaffold, [])

        self.assertListEqual(list(mock_create_paths.call_args[0][0]), list(PATHS.values()))

    @patch("pymake.write_templates.create_paths")
    @patch("pymake.write_templates.write_templates")
    @patch("pymake.write_templates.Path.cwd")
    def test_podman_scaffold_write_templates_called(self, mock_cwd, mock_write_templates, mock_create_paths):
        runner = CliRunner()
        runner.invoke(podman_scaffold, [])

        mock_write_templates.assert_called_once_with(TEMPLATES, False)

    @patch("pymake.write_templates.create_paths")
    @patch("pymake.write_templates.write_templates")
    @patch("pymake.write_templates.Path.cwd")
    def test_podman_scaffold_current_directory(self, mock_cwd, mock_write_templates, mock_create_paths):
        mock_cwd.return_value = Path("/mocked/path")
        runner = CliRunner()
        runner.invoke(podman_scaffold, [])

        mock_cwd.assert_called_once()
        self.assertEqual(mock_cwd.return_value, Path("/mocked/path"))


if __name__ == "__main__":
    unittest.main()
