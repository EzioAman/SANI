"""Content-based security scanner for detecting secrets and vulnerabilities before Git operations.

Scans actual file contents — not just filenames — for API keys, passwords, private keys,
connection strings, and other sensitive data that should never reach a remote repository.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Finding:
    """A single security finding in a specific file."""

    file: str
    line: int
    severity: Severity
    category: str
    snippet: str
    message: str


@dataclass
class ScanReport:
    """Aggregated results from a security scan."""

    findings: list[Finding] = field(default_factory=list)
    scanned_count: int = 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)

    @property
    def is_clean(self) -> bool:
        return self.critical_count == 0

    def blocked_files(self) -> set[str]:
        """Return set of file paths that have CRITICAL findings and must be excluded."""
        return {f.file for f in self.findings if f.severity == Severity.CRITICAL}

    def warned_files(self) -> set[str]:
        """Return set of file paths that have WARNING findings."""
        return {f.file for f in self.findings if f.severity == Severity.WARNING}


# --- Pattern Definitions ---

# Filename patterns that are always blocked (never pushed)
_BLOCKED_FILENAME_PATTERNS: list[tuple[str, str]] = [
    (r"\.env$", "Environment variable file"),
    (r"\.env\.\w+$", "Environment variable file"),
    (r"\.db$", "Database file"),
    (r"\.sqlite3?$", "SQLite database file"),
    (r"sani_memory\.db", "SANI memory database"),
    (r"\.pem$", "PEM certificate/key file"),
    (r"\.key$", "Private key file"),
    (r"\.pfx$", "PKCS#12 certificate file"),
    (r"\.p12$", "PKCS#12 certificate file"),
    (r"id_rsa$", "SSH private key"),
    (r"id_ed25519$", "SSH private key"),
    (r"id_ecdsa$", "SSH private key"),
    (r"\.keystore$", "Java keystore file"),
    (r"\.jks$", "Java keystore file"),
]

# Content patterns scanned inside files (regex, severity, category, message)
_CONTENT_PATTERNS: list[tuple[str, Severity, str, str]] = [
    # Google / Gemini API keys
    (r"AIza[0-9A-Za-z_-]{35}", Severity.CRITICAL, "api_key", "Google/Gemini API key detected"),
    # OpenAI API keys
    (r"sk-[A-Za-z0-9]{20,}", Severity.CRITICAL, "api_key", "OpenAI API key detected"),
    # GitHub tokens
    (r"ghp_[A-Za-z0-9]{36}", Severity.CRITICAL, "api_key", "GitHub personal access token detected"),
    (r"gho_[A-Za-z0-9]{36}", Severity.CRITICAL, "api_key", "GitHub OAuth token detected"),
    (r"github_pat_[A-Za-z0-9_]{22,}", Severity.CRITICAL, "api_key", "GitHub fine-grained token detected"),
    # AWS access keys
    (r"AKIA[0-9A-Z]{16}", Severity.CRITICAL, "api_key", "AWS access key ID detected"),
    # Generic secret assignment patterns
    (
        r"""(?:password|passwd|pwd|secret|token|api_key|apikey|auth_token|access_token)\s*[=:]\s*["'][^"']{8,}["']""",
        Severity.CRITICAL,
        "password",
        "Hardcoded password or secret detected",
    ),
    # Private key blocks
    (r"-----BEGIN\s+(?:RSA\s+)?PRIVATE KEY-----", Severity.CRITICAL, "private_key", "Private key block detected"),
    (r"-----BEGIN\s+EC\s+PRIVATE KEY-----", Severity.CRITICAL, "private_key", "EC private key block detected"),
    (r"-----BEGIN\s+DSA\s+PRIVATE KEY-----", Severity.CRITICAL, "private_key", "DSA private key block detected"),
    # Connection strings with embedded credentials
    (
        r"(?:mysql|postgres|postgresql|mongodb|redis|amqp)://[^:]+:[^@]+@",
        Severity.CRITICAL,
        "connection_string",
        "Connection string with embedded credentials detected",
    ),
    # Security-related TODOs
    (
        r"#\s*(?:TODO|FIXME|HACK|XXX).*(?:secret|token|password|key|credential|remove|hardcod)",
        Severity.WARNING,
        "security_todo",
        "Security-related TODO comment found",
    ),
]

# Large binary file extensions that shouldn't be in a repo
_BINARY_EXTENSIONS: set[str] = {
    ".exe", ".dll", ".so", ".dylib", ".bin", ".dat",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".msi", ".dmg", ".iso",
}

# Max file size for content scanning (skip very large files)
_MAX_SCAN_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB
# Large binary warning threshold
_LARGE_BINARY_THRESHOLD = 5 * 1024 * 1024  # 5 MB


class SecurityScanner:
    """Scans file contents for secrets, credentials, and security vulnerabilities."""

    def __init__(self) -> None:
        self._compiled_content_patterns = [
            (re.compile(pattern, re.IGNORECASE), severity, category, message)
            for pattern, severity, category, message in _CONTENT_PATTERNS
        ]
        self._compiled_filename_patterns = [
            (re.compile(pattern, re.IGNORECASE), message)
            for pattern, message in _BLOCKED_FILENAME_PATTERNS
        ]

    def _mask_secret(self, text: str, max_visible: int = 6) -> str:
        """Mask a secret string, showing only a few characters."""
        text = text.strip().strip("\"'")
        if len(text) <= max_visible:
            return "***"
        return text[:max_visible] + "..." + "*" * min(8, len(text) - max_visible)

    def scan_filename(self, filepath: str) -> list[Finding]:
        """Check if a filename itself is a blocked pattern."""
        basename = os.path.basename(filepath).lower()
        findings: list[Finding] = []
        for pattern, message in self._compiled_filename_patterns:
            if pattern.search(basename):
                findings.append(Finding(
                    file=filepath, line=0, severity=Severity.CRITICAL,
                    category="sensitive_file", snippet=basename, message=message,
                ))
                break
        return findings

    def scan_file_content(self, filepath: str, root: Path) -> list[Finding]:
        """Scan a single file's contents for secret patterns."""
        full_path = root / filepath
        findings: list[Finding] = []

        # Check file extension for large binaries
        ext = full_path.suffix.lower()
        if ext in _BINARY_EXTENSIONS:
            try:
                size = full_path.stat().st_size
                if size > _LARGE_BINARY_THRESHOLD:
                    findings.append(Finding(
                        file=filepath, line=0, severity=Severity.WARNING,
                        category="large_binary",
                        snippet=f"{size / (1024*1024):.1f} MB",
                        message=f"Large binary file ({ext})",
                    ))
            except OSError:
                pass
            return findings  # Don't scan binary content

        # Skip files too large for content scan
        try:
            if full_path.stat().st_size > _MAX_SCAN_SIZE_BYTES:
                return findings
        except OSError:
            return findings

        # Read and scan content
        try:
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            return findings

        for line_num, line in enumerate(content.splitlines(), start=1):
            for pattern, severity, category, message in self._compiled_content_patterns:
                match = pattern.search(line)
                if match:
                    snippet = self._mask_secret(match.group(0))
                    findings.append(Finding(
                        file=filepath, line=line_num, severity=severity,
                        category=category, snippet=snippet, message=message,
                    ))
                    break  # One finding per line is enough

        return findings

    def scan_workspace(self, root: Path, files: list[str]) -> ScanReport:
        """Scan a list of files for security vulnerabilities.

        Args:
            root: Workspace root directory.
            files: List of file paths relative to root.

        Returns:
            ScanReport with all findings.
        """
        report = ScanReport(scanned_count=len(files))

        for filepath in files:
            # 1. Check filename
            report.findings.extend(self.scan_filename(filepath))

            # 2. Check file contents
            report.findings.extend(self.scan_file_content(filepath, root))

        return report
