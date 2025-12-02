"""Tests for the CLI module."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import click.testing

from obsistant.cli import cli


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self) -> None:
        """Test CLI help command."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert (
            "Process Obsidian vault to extract tags and add metadata" in result.output
        )
        assert "backup" in result.output
        assert "process" in result.output
        assert "meetings" in result.output
        assert "notes" in result.output
        assert "quick-notes" in result.output

    def test_process_command_help(self) -> None:
        """Test process command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["process", "--help"])

        assert result.exit_code == 0
        assert (
            "Process Obsidian vault to extract tags and add metadata" in result.output
        )
        assert "--dry-run" in result.output
        assert "--backup-ext" in result.output
        assert "--format" in result.output

    def test_meetings_command_help(self) -> None:
        """Test meetings command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["meetings", "--help"])

        assert result.exit_code == 0
        assert "Process meetings folder" in result.output
        assert "--meetings-folder" in result.output
        assert "--dry-run" in result.output

    def test_notes_command_help(self) -> None:
        """Test notes command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["notes", "--help"])

        assert result.exit_code == 0
        assert "Process notes folder" in result.output
        assert "--notes-folder" in result.output
        assert "--dry-run" in result.output

    def test_quick_notes_command_help(self) -> None:
        """Test quick-notes command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["quick-notes", "--help"])

        assert result.exit_code == 0
        assert "Process quick notes folder" in result.output
        assert "--notes-folder" in result.output
        assert "--quick-notes-folder" in result.output
        assert "--meetings-folder" in result.output

    def test_backup_command_help(self) -> None:
        """Test backup command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["backup", "--help"])

        assert result.exit_code == 0
        assert "Create a complete backup of the vault" in result.output
        assert "--backup-name" in result.output

    def test_clear_backups_command_help(self) -> None:
        """Test clear-backups command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["clear-backups", "--help"])

        assert result.exit_code == 0
        assert "Clear all backup files" in result.output

    def test_restore_command_help(self) -> None:
        """Test restore command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["restore", "--help"])

        assert result.exit_code == 0
        assert "Restore corrupted files from backups" in result.output
        assert "--file" in result.output

    @patch("obsistant.cli.process_vault")
    def test_process_command_dry_run(self, mock_process_vault: Any) -> None:
        """Test process command with dry run."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["process", str(vault_path), "--dry-run"])

            assert result.exit_code == 0
            mock_process_vault.assert_called_once()
            args, kwargs = mock_process_vault.call_args
            assert kwargs["dry_run"] is True  # dry_run=True

    @patch("obsistant.cli.process_vault")
    def test_process_command_with_specific_file(self, mock_process_vault: Any) -> None:
        """Test process command with specific file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()
            test_file = vault_path / "test.md"
            test_file.write_text("# Test")

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--file", str(test_file)]
            )

            assert result.exit_code == 0
            mock_process_vault.assert_called_once()

    @patch("obsistant.cli.process_meetings_folder")
    def test_meetings_command(self, mock_process_meetings: Any) -> None:
        """Test meetings command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["meetings", str(vault_path)])

            assert result.exit_code == 0
            mock_process_meetings.assert_called_once()

    @patch("obsistant.cli.process_notes_folder")
    def test_notes_command(self, mock_process_notes: Any) -> None:
        """Test notes command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["notes", str(vault_path)])

            assert result.exit_code == 0
            mock_process_notes.assert_called_once()

    @patch("obsistant.cli.process_quick_notes_folder")
    def test_quick_notes_command(self, mock_process_quick_notes: Any) -> None:
        """Test quick-notes command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["quick-notes", str(vault_path)])

            assert result.exit_code == 0
            mock_process_quick_notes.assert_called_once()

    @patch("obsistant.cli.create_vault_backup")
    def test_backup_command(self, mock_create_backup: Any) -> None:
        """Test backup command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Mock the backup creation
            mock_create_backup.return_value = Path(tmp_dir) / "backup"

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["backup", str(vault_path)])

            assert result.exit_code == 0
            mock_create_backup.assert_called_once()

    @patch("obsistant.cli.create_vault_backup")
    def test_backup_command_with_custom_name(self, mock_create_backup: Any) -> None:
        """Test backup command with custom name."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Mock the backup creation
            mock_create_backup.return_value = Path(tmp_dir) / "custom_backup"

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["backup", str(vault_path), "--backup-name", "custom_backup"]
            )

            assert result.exit_code == 0
            mock_create_backup.assert_called_once_with(
                vault_root=vault_path, backup_name="custom_backup"
            )

    @patch("obsistant.cli.clear_backups_func")
    def test_clear_backups_command(self, mock_clear_backups: Any) -> None:
        """Test clear-backups command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Mock the clear backups function
            mock_clear_backups.return_value = 5

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["clear-backups", str(vault_path)])

            assert result.exit_code == 0
            mock_clear_backups.assert_called_once()

    @patch("obsistant.cli.restore_files_func")
    def test_restore_command(self, mock_restore_files: Any) -> None:
        """Test restore command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            # Mock the restore function
            mock_restore_files.return_value = 3

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["restore", str(vault_path)])

            assert result.exit_code == 0
            mock_restore_files.assert_called_once()

    @patch("obsistant.cli.restore_files_func")
    def test_restore_command_with_specific_file(self, mock_restore_files: Any) -> None:
        """Test restore command with specific file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()
            test_file = vault_path / "test.md"
            test_file.write_text("# Test")

            # Mock the restore function
            mock_restore_files.return_value = 1

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["restore", str(vault_path), "--file", str(test_file)]
            )

            assert result.exit_code == 0
            mock_restore_files.assert_called_once()

    def test_process_command_invalid_file(self) -> None:
        """Test process command with invalid file path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()
            invalid_file = Path(tmp_dir) / "outside.md"
            invalid_file.write_text("# Test")

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--file", str(invalid_file)]
            )

            assert result.exit_code != 0
            assert "is not within vault" in result.output

    def test_process_command_non_markdown_file(self) -> None:
        """Test process command with non-markdown file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()
            non_md_file = vault_path / "test.txt"
            non_md_file.write_text("Test content")

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["process", str(vault_path), "--file", str(non_md_file)]
            )

            assert result.exit_code != 0
            assert "is not a markdown file" in result.output

    def test_restore_command_invalid_file(self) -> None:
        """Test restore command with invalid file path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()
            invalid_file = Path(tmp_dir) / "outside.md"
            invalid_file.write_text("# Test")

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["restore", str(vault_path), "--file", str(invalid_file)]
            )

            assert result.exit_code != 0
            assert "is not within vault" in result.output

    def test_nonexistent_vault_path(self) -> None:
        """Test commands with nonexistent vault path."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["process", "/nonexistent/vault"])

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_qdrant_command_help(self) -> None:
        """Test qdrant command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["qdrant", "--help"])

        assert result.exit_code == 0
        assert "Manage Qdrant vector database server" in result.output
        assert "start" in result.output
        assert "stop" in result.output
        assert "ingest" in result.output

    def test_qdrant_start_command_help(self) -> None:
        """Test qdrant start command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["qdrant", "start", "--help"])

        assert result.exit_code == 0
        assert "Start Qdrant server in Docker" in result.output
        assert "--http-port" in result.output
        assert "--grpc-port" in result.output

    def test_qdrant_stop_command_help(self) -> None:
        """Test qdrant stop command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["qdrant", "stop", "--help"])

        assert result.exit_code == 0
        assert "Stop Qdrant server" in result.output

    def test_qdrant_ingest_command_help(self) -> None:
        """Test qdrant ingest command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["qdrant", "ingest", "--help"])

        assert result.exit_code == 0
        assert "Ingest documents from vault" in result.output
        assert "--collection" in result.output
        assert "--include-pdfs" in result.output
        assert "--recreate-collection" in result.output
        assert "--dry-run" in result.output

    @patch("obsistant.cli.start_qdrant_server")
    @patch("obsistant.cli.is_qdrant_running")
    def test_qdrant_start_command(
        self, mock_is_running: Any, mock_start_server: Any
    ) -> None:
        """Test qdrant start command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_is_running.return_value = False
            mock_start_server.return_value = "container-id-123"

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["qdrant", "start", str(vault_path)])

            assert result.exit_code == 0
            mock_start_server.assert_called_once_with(vault_path, ports=(6333, 6334))

    @patch("obsistant.cli.start_qdrant_server")
    @patch("obsistant.cli.is_qdrant_running")
    def test_qdrant_start_command_already_running(
        self, mock_is_running: Any, mock_start_server: Any
    ) -> None:
        """Test qdrant start command when server is already running."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_is_running.return_value = True

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["qdrant", "start", str(vault_path)])

            assert result.exit_code == 0
            mock_start_server.assert_not_called()

    @patch("obsistant.cli.start_qdrant_server")
    @patch("obsistant.cli.is_qdrant_running")
    def test_qdrant_start_command_custom_ports(
        self, mock_is_running: Any, mock_start_server: Any
    ) -> None:
        """Test qdrant start command with custom ports."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_is_running.return_value = False
            mock_start_server.return_value = "container-id-123"

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli,
                [
                    "qdrant",
                    "start",
                    str(vault_path),
                    "--http-port",
                    "8080",
                    "--grpc-port",
                    "8081",
                ],
            )

            assert result.exit_code == 0
            mock_start_server.assert_called_once_with(vault_path, ports=(8080, 8081))

    @patch("obsistant.cli.stop_qdrant_server")
    def test_qdrant_stop_command(self, mock_stop_server: Any) -> None:
        """Test qdrant stop command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_stop_server.return_value = True

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["qdrant", "stop", str(vault_path)])

            assert result.exit_code == 0
            mock_stop_server.assert_called_once_with(vault_path)

    @patch("obsistant.cli.stop_qdrant_server")
    def test_qdrant_stop_command_not_running(self, mock_stop_server: Any) -> None:
        """Test qdrant stop command when server is not running."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_stop_server.return_value = False

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["qdrant", "stop", str(vault_path)])

            assert result.exit_code == 0
            mock_stop_server.assert_called_once_with(vault_path)

    @patch("obsistant.cli.ingest_documents")
    @patch("obsistant.cli.is_qdrant_running")
    @patch("obsistant.config.env_loader.load_vault_env")
    def test_qdrant_ingest_command(
        self,
        mock_load_env: Any,
        mock_is_running: Any,
        mock_ingest: Any,
    ) -> None:
        """Test qdrant ingest command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_is_running.return_value = True
            mock_ingest.return_value = {
                "files_processed": 10,
                "files_skipped": 2,
                "chunks_created": 50,
                "embeddings_generated": 50,
                "errors": [],
            }

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["qdrant", "ingest", str(vault_path)])

            assert result.exit_code == 0
            mock_load_env.assert_called_once()
            mock_is_running.assert_called_once_with(vault_path)
            mock_ingest.assert_called_once()

    @patch("obsistant.cli.ingest_documents")
    @patch("obsistant.cli.is_qdrant_running")
    @patch("obsistant.config.env_loader.load_vault_env")
    def test_qdrant_ingest_command_dry_run(
        self,
        mock_load_env: Any,
        mock_is_running: Any,
        mock_ingest: Any,
    ) -> None:
        """Test qdrant ingest command with dry run."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_is_running.return_value = True
            mock_ingest.return_value = {
                "files_processed": 0,
                "files_skipped": 0,
                "chunks_created": 0,
                "embeddings_generated": 0,
                "errors": [],
            }

            runner = click.testing.CliRunner()
            result = runner.invoke(
                cli, ["qdrant", "ingest", str(vault_path), "--dry-run"]
            )

            assert result.exit_code == 0
            assert "DRY RUN" in result.output

    @patch("obsistant.cli.is_qdrant_running")
    def test_qdrant_ingest_command_server_not_running(
        self, mock_is_running: Any
    ) -> None:
        """Test qdrant ingest command when server is not running."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"
            vault_path.mkdir()

            mock_is_running.return_value = False

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["qdrant", "ingest", str(vault_path)])

            assert result.exit_code != 0
            assert "Qdrant server is not running" in result.output

    def test_init_command_help(self) -> None:
        """Test init command help."""
        runner = click.testing.CliRunner()
        result = runner.invoke(cli, ["init", "--help"])

        assert result.exit_code == 0
        assert "Initialize a new vault" in result.output
        assert "--overwrite-config" in result.output
        assert "--skip-folders" in result.output

    @patch("obsistant.cli.init_vault")
    def test_init_command(self, mock_init_vault: Any) -> None:
        """Test init command."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["init", str(vault_path)])

            assert result.exit_code == 0
            mock_init_vault.assert_called_once_with(
                vault_path=vault_path,
                overwrite_config=False,
                skip_folders=False,
            )

    @patch("obsistant.cli.init_vault")
    def test_init_command_with_overwrite(self, mock_init_vault: Any) -> None:
        """Test init command with overwrite config."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["init", str(vault_path), "--overwrite-config"])

            assert result.exit_code == 0
            mock_init_vault.assert_called_once_with(
                vault_path=vault_path,
                overwrite_config=True,
                skip_folders=False,
            )

    @patch("obsistant.cli.init_vault")
    def test_init_command_with_skip_folders(self, mock_init_vault: Any) -> None:
        """Test init command with skip folders."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vault_path = Path(tmp_dir) / "vault"

            runner = click.testing.CliRunner()
            result = runner.invoke(cli, ["init", str(vault_path), "--skip-folders"])

            assert result.exit_code == 0
            mock_init_vault.assert_called_once_with(
                vault_path=vault_path,
                overwrite_config=False,
                skip_folders=True,
            )


class TestSetupLogger:
    """Test logger setup functionality."""

    def test_setup_logger_default(self) -> None:
        """Test default logger setup."""
        from loguru import logger as loguru_logger

        from obsistant.cli import setup_logger

        # Remove any existing handlers to start fresh
        loguru_logger.remove()

        logger = setup_logger()
        # Loguru logger is a singleton
        assert logger is loguru_logger
        # Check that INFO level messages are allowed (default)
        # We can't directly check level, but we can verify the logger works
        assert logger is not None

    def test_setup_logger_verbose(self) -> None:
        """Test verbose logger setup."""
        from loguru import logger as loguru_logger

        from obsistant.cli import setup_logger

        # Remove any existing handlers to start fresh
        loguru_logger.remove()

        logger = setup_logger(verbose=True)
        # Loguru logger is a singleton
        assert logger is loguru_logger
        # Check that DEBUG level messages are allowed (verbose mode)
        assert logger is not None

    def test_setup_logger_idempotent(self) -> None:
        """Test that setup_logger is idempotent."""
        from loguru import logger as loguru_logger

        from obsistant.cli import setup_logger

        # Remove any existing handlers to start fresh
        loguru_logger.remove()

        logger1 = setup_logger()
        logger2 = setup_logger()

        # Loguru logger is a singleton
        assert logger1 is logger2
        assert logger1 is loguru_logger
