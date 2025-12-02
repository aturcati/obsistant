"""Tests for Google Calendar OAuth authentication."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from obsistant.core.calendar_auth import authenticate_google_calendar


class TestAuthenticateGoogleCalendar:
    """Test authenticate_google_calendar function."""

    @patch("obsistant.core.calendar_auth.Credentials")
    def test_authenticate_with_valid_existing_token(
        self, mock_credentials_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test authentication with valid existing token."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        token_path.parent.mkdir(parents=True)
        credentials_path = vault_path / ".obsistant" / "credentials.json"

        # Create token file
        token_path.write_text('{"token": "valid_token"}')

        # Mock valid credentials
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds

        result = authenticate_google_calendar(vault_path, credentials_path, token_path)

        assert result == mock_creds
        mock_credentials_class.from_authorized_user_file.assert_called_once()

    @patch("obsistant.core.calendar_auth.Credentials")
    @patch("obsistant.core.calendar_auth.Request")
    def test_authenticate_refreshes_expired_token(
        self,
        mock_request_class: MagicMock,
        mock_credentials_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test authentication refreshes expired token."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        token_path.parent.mkdir(parents=True)
        credentials_path = vault_path / ".obsistant" / "credentials.json"

        # Create token file
        token_path.write_text('{"token": "expired_token"}')

        # Mock expired credentials that can be refreshed
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_value"
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds

        # After refresh, credentials become valid
        def refresh_side_effect(*args, **kwargs):
            mock_creds.valid = True
            mock_creds.expired = False

        mock_request = MagicMock()
        mock_request_class.return_value = mock_request
        mock_creds.refresh.side_effect = refresh_side_effect
        mock_creds.to_json.return_value = '{"token": "refreshed_token"}'

        result = authenticate_google_calendar(vault_path, credentials_path, token_path)

        assert result == mock_creds
        assert result.valid is True
        mock_creds.refresh.assert_called_once_with(mock_request)
        # Should save refreshed token
        assert token_path.exists()

    @patch("obsistant.core.calendar_auth.Credentials")
    @patch("obsistant.core.calendar_auth.InstalledAppFlow")
    def test_authenticate_runs_oauth_flow_when_no_token(
        self,
        mock_flow_class: MagicMock,
        mock_credentials_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test authentication runs OAuth flow when no token exists."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        credentials_path = vault_path / ".obsistant" / "credentials.json"
        credentials_path.parent.mkdir(parents=True)

        # Create credentials file
        credentials_path.write_text('{"client_id": "test_id"}')

        # No token file exists
        assert not token_path.exists()

        # Mock OAuth flow
        mock_flow = MagicMock()
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.to_json.return_value = '{"token": "new_token"}'
        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        result = authenticate_google_calendar(vault_path, credentials_path, token_path)

        assert result == mock_creds
        mock_flow_class.from_client_secrets_file.assert_called_once()
        mock_flow.run_local_server.assert_called_once_with(port=0)
        # Should save token
        assert token_path.exists()

    @patch("obsistant.core.calendar_auth.Credentials")
    @patch("obsistant.core.calendar_auth.InstalledAppFlow")
    def test_authenticate_runs_oauth_flow_when_token_invalid(
        self,
        mock_flow_class: MagicMock,
        mock_credentials_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test authentication runs OAuth flow when token is invalid and can't be refreshed."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        token_path.parent.mkdir(parents=True)
        credentials_path = vault_path / ".obsistant" / "credentials.json"
        credentials_path.write_text('{"client_id": "test_id"}')

        # Create invalid token file
        token_path.write_text('{"token": "invalid_token"}')

        # Mock invalid credentials that can't be refreshed
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = None  # No refresh token
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds

        # Mock OAuth flow
        mock_flow = MagicMock()
        mock_new_creds = MagicMock()
        mock_new_creds.valid = True
        mock_new_creds.to_json.return_value = '{"token": "new_token"}'
        mock_flow.run_local_server.return_value = mock_new_creds
        mock_flow_class.from_client_secrets_file.return_value = mock_flow

        result = authenticate_google_calendar(vault_path, credentials_path, token_path)

        assert result == mock_new_creds
        # Should not try to refresh (no refresh_token)
        mock_creds.refresh.assert_not_called()

    @patch("obsistant.core.calendar_auth.Credentials")
    @patch("obsistant.core.calendar_auth.Request")
    def test_authenticate_handles_refresh_failure(
        self,
        mock_request_class: MagicMock,
        mock_credentials_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test authentication handles refresh failure and falls back to OAuth."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        token_path.parent.mkdir(parents=True)
        credentials_path = vault_path / ".obsistant" / "credentials.json"
        credentials_path.write_text('{"client_id": "test_id"}')

        # Create token file
        token_path.write_text('{"token": "expired_token"}')

        # Mock expired credentials that fail to refresh
        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_value"
        mock_credentials_class.from_authorized_user_file.return_value = mock_creds

        mock_request = MagicMock()
        mock_request_class.return_value = mock_request
        mock_creds.refresh.side_effect = Exception("Refresh failed")

        # Mock OAuth flow as fallback
        from unittest.mock import patch as mock_patch

        with mock_patch(
            "obsistant.core.calendar_auth.InstalledAppFlow"
        ) as mock_flow_class:
            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.valid = True
            mock_new_creds.to_json.return_value = '{"token": "new_token"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_class.from_client_secrets_file.return_value = mock_flow

            result = authenticate_google_calendar(
                vault_path, credentials_path, token_path
            )

            assert result == mock_new_creds
            # Should have tried to refresh first
            mock_creds.refresh.assert_called_once()

    def test_authenticate_raises_error_when_credentials_missing(
        self, tmp_path: Path
    ) -> None:
        """Test authentication raises error when credentials.json is missing."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        credentials_path = vault_path / ".obsistant" / "credentials.json"

        # No credentials file
        assert not credentials_path.exists()

        with pytest.raises(FileNotFoundError, match="credentials.json not found"):
            authenticate_google_calendar(vault_path, credentials_path, token_path)

    @patch("obsistant.core.calendar_auth.Credentials")
    def test_authenticate_handles_invalid_token_file(
        self, mock_credentials_class: MagicMock, tmp_path: Path
    ) -> None:
        """Test authentication handles invalid token file gracefully."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        token_path = vault_path / ".obsistant" / "token.json"
        token_path.parent.mkdir(parents=True)
        credentials_path = vault_path / ".obsistant" / "credentials.json"
        credentials_path.write_text('{"client_id": "test_id"}')

        # Create invalid token file
        token_path.write_text("invalid json content")

        # Mock that loading fails
        mock_credentials_class.from_authorized_user_file.side_effect = Exception(
            "Invalid token file"
        )

        # Mock OAuth flow as fallback
        from unittest.mock import patch as mock_patch

        with mock_patch(
            "obsistant.core.calendar_auth.InstalledAppFlow"
        ) as mock_flow_class:
            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.valid = True
            mock_new_creds.to_json.return_value = '{"token": "new_token"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_class.from_client_secrets_file.return_value = mock_flow

            result = authenticate_google_calendar(
                vault_path, credentials_path, token_path
            )

            assert result == mock_new_creds
            # Should have tried to load token but failed, then run OAuth

    def test_authenticate_resolves_relative_paths(self, tmp_path: Path) -> None:
        """Test authentication resolves relative paths correctly."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        credentials_path = Path(".obsistant/credentials.json")  # Relative
        token_path = Path(".obsistant/token.json")  # Relative

        # Create credentials file at resolved path
        resolved_credentials = vault_path / credentials_path
        resolved_credentials.parent.mkdir(parents=True)
        resolved_credentials.write_text('{"client_id": "test_id"}')

        # Mock OAuth flow
        from unittest.mock import patch as mock_patch

        with mock_patch(
            "obsistant.core.calendar_auth.InstalledAppFlow"
        ) as mock_flow_class:
            mock_flow = MagicMock()
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_creds.to_json.return_value = '{"token": "new_token"}'
            mock_flow.run_local_server.return_value = mock_creds
            mock_flow_class.from_client_secrets_file.return_value = mock_flow

            result = authenticate_google_calendar(
                vault_path, credentials_path, token_path
            )

            assert result == mock_creds
            # Should have resolved paths relative to vault_path
            resolved_token = vault_path / token_path
            assert resolved_token.exists()

    def test_authenticate_uses_absolute_paths(self, tmp_path: Path) -> None:
        """Test authentication uses absolute paths as-is."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        credentials_path = tmp_path / "absolute" / "credentials.json"
        token_path = tmp_path / "absolute" / "token.json"
        credentials_path.parent.mkdir(parents=True)
        credentials_path.write_text('{"client_id": "test_id"}')

        # Mock OAuth flow
        from unittest.mock import patch as mock_patch

        with mock_patch(
            "obsistant.core.calendar_auth.InstalledAppFlow"
        ) as mock_flow_class:
            mock_flow = MagicMock()
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_creds.to_json.return_value = '{"token": "new_token"}'
            mock_flow.run_local_server.return_value = mock_creds
            mock_flow_class.from_client_secrets_file.return_value = mock_flow

            result = authenticate_google_calendar(
                vault_path, credentials_path, token_path
            )

            assert result == mock_creds
            # Should use absolute paths as-is
            assert token_path.exists()
