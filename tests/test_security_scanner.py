"""Tests for content-based security scanner."""

import os
from pathlib import Path
import pytest
from sani.tools.security_scanner import SecurityScanner, Severity


@pytest.fixture
def scanner() -> SecurityScanner:
    return SecurityScanner()


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    return tmp_path


def _write(ws: Path, rel_path: str, content: str) -> None:
    full = ws / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")


# --- Filename Pattern Tests ---

def test_env_file_blocked(scanner: SecurityScanner) -> None:
    findings = scanner.scan_filename(".env")
    assert len(findings) == 1
    assert findings[0].severity == Severity.CRITICAL
    assert findings[0].category == "sensitive_file"


def test_env_local_blocked(scanner: SecurityScanner) -> None:
    findings = scanner.scan_filename(".env.local")
    assert len(findings) == 1
    assert findings[0].severity == Severity.CRITICAL


def test_db_file_blocked(scanner: SecurityScanner) -> None:
    findings = scanner.scan_filename("sani_memory.db")
    assert len(findings) >= 1
    assert all(f.severity == Severity.CRITICAL for f in findings)


def test_pem_file_blocked(scanner: SecurityScanner) -> None:
    findings = scanner.scan_filename("server.pem")
    assert len(findings) == 1
    assert findings[0].severity == Severity.CRITICAL


def test_clean_file_not_blocked(scanner: SecurityScanner) -> None:
    findings = scanner.scan_filename("agent.py")
    assert len(findings) == 0


# --- Content Pattern Tests ---

def test_detects_google_api_key(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "config.py", 'API_KEY = "AIzaSyA1234567890abcdefghijklmnopqrstuv"\n')
    report = scanner.scan_workspace(tmp_workspace, ["config.py"])
    assert report.critical_count >= 1
    assert any(f.category == "api_key" for f in report.findings)


def test_detects_openai_key(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "settings.py", 'OPENAI_KEY = "sk-abcdefghijklmnopqrstuvwxyz1234567890"\n')
    report = scanner.scan_workspace(tmp_workspace, ["settings.py"])
    assert report.critical_count >= 1


def test_detects_github_token(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "deploy.sh", 'TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890\n')
    report = scanner.scan_workspace(tmp_workspace, ["deploy.sh"])
    assert report.critical_count >= 1


def test_detects_password_assignment(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "db.py", 'password = "super_secret_password_123"\n')
    report = scanner.scan_workspace(tmp_workspace, ["db.py"])
    assert report.critical_count >= 1
    assert any(f.category == "password" for f in report.findings)


def test_detects_private_key_block(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "key.txt", "-----BEGIN RSA PRIVATE KEY-----\nMIIE...\n-----END RSA PRIVATE KEY-----\n")
    report = scanner.scan_workspace(tmp_workspace, ["key.txt"])
    assert report.critical_count >= 1
    assert any(f.category == "private_key" for f in report.findings)


def test_detects_connection_string(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "config.ini", "DATABASE_URL=postgres://admin:p4ssw0rd@db.example.com:5432/mydb\n")
    report = scanner.scan_workspace(tmp_workspace, ["config.ini"])
    assert report.critical_count >= 1
    assert any(f.category == "connection_string" for f in report.findings)


def test_detects_security_todo(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "auth.py", "# TODO: remove hardcoded token before release\ntoken = get_env('TOKEN')\n")
    report = scanner.scan_workspace(tmp_workspace, ["auth.py"])
    assert report.warning_count >= 1
    assert any(f.category == "security_todo" for f in report.findings)


def test_clean_file_passes(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, "clean.py", "def hello():\n    return 'world'\n")
    report = scanner.scan_workspace(tmp_workspace, ["clean.py"])
    assert report.is_clean
    assert report.critical_count == 0
    assert report.warning_count == 0


def test_blocked_files_set(scanner: SecurityScanner, tmp_workspace: Path) -> None:
    _write(tmp_workspace, ".env", "SECRET=abc123\n")
    _write(tmp_workspace, "main.py", "print('hello')\n")
    report = scanner.scan_workspace(tmp_workspace, [".env", "main.py"])
    blocked = report.blocked_files()
    assert ".env" in blocked
    assert "main.py" not in blocked


def test_masked_secrets(scanner: SecurityScanner) -> None:
    masked = scanner._mask_secret("AIzaSyA1234567890abcdefghijklmnopqrstuv")
    assert masked.startswith("AIzaSy")
    assert "..." in masked
    # Should NOT contain the full key
    assert "abcdefghijklmnopqrstuv" not in masked
