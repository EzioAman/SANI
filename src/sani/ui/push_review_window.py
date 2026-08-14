"""Interactive Push Review Window — Dark-themed GUI with file checklist and security badges.

Opens a customtkinter window showing:
- Branch/remote info
- Scrollable file checklist with checkboxes
- Security scan results with severity badges
- Commit message input
- Confirm/Cancel buttons

All elements are voice-controllable via public methods.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from sani.tools.security_scanner import ScanReport


@dataclass
class PushStatus:
    """Git status context for the review window."""

    branch: str = "main"
    remote_url: str = ""
    commits_ahead: int = 0
    changed_files: list[dict] = field(default_factory=list)
    # Each dict: {"path": str, "status": "modified"|"new"|"deleted"|"untracked"}


@dataclass
class PushDecision:
    """User's decision from the review window."""

    cancelled: bool = False
    selected_files: list[str] = field(default_factory=list)
    commit_message: str = ""


class PushReviewWindow:
    """CustomTkinter GUI for reviewing and selecting files before a push.

    Thread-safety: The window runs on whatever thread calls `open()`.
    Voice/background updates use `_schedule(fn)` which calls `after(0, fn)`.
    """

    def __init__(self) -> None:
        self._root: ctk.CTk | None = None
        self._decision: PushDecision | None = None
        self._result_event = threading.Event()
        self._checkboxes: list[tuple[ctk.CTkCheckBox, ctk.StringVar, str]] = []
        self._blocked_files: set[str] = set()
        self._commit_entry: ctk.CTkTextbox | None = None

    # --- Public API (voice-callable) ---

    def open(self, status: PushStatus, scan: "ScanReport") -> None:
        """Build and display the review window. Blocks until user decides."""
        self._build_window(status, scan)
        if self._root:
            self._root.mainloop()

    def wait_for_result(self) -> PushDecision:
        """Block until the user confirms or cancels. Returns the decision."""
        self._result_event.wait()
        return self._decision or PushDecision(cancelled=True)

    def toggle_file(self, index: int) -> None:
        """Toggle checkbox at given index (0-based). Voice: 'toggle file 3'."""
        if 0 <= index < len(self._checkboxes):
            cb, var, path = self._checkboxes[index]
            if path in self._blocked_files:
                return  # Cannot toggle blocked files
            self._schedule(lambda: var.set("0" if var.get() == "1" else "1"))

    def exclude_file(self, name: str) -> None:
        """Uncheck a file by partial name match. Voice: 'exclude the database'."""
        name_lower = name.lower()
        for cb, var, path in self._checkboxes:
            if name_lower in path.lower() and path not in self._blocked_files:
                self._schedule(lambda v=var: v.set("0"))

    def include_file(self, name: str) -> None:
        """Check a file by partial name match. Voice: 'include config'."""
        name_lower = name.lower()
        for cb, var, path in self._checkboxes:
            if name_lower in path.lower() and path not in self._blocked_files:
                self._schedule(lambda v=var: v.set("1"))

    def select_all(self) -> None:
        """Check all non-blocked files. Voice: 'select all'."""
        for cb, var, path in self._checkboxes:
            if path not in self._blocked_files:
                self._schedule(lambda v=var: v.set("1"))

    def deselect_all(self) -> None:
        """Uncheck all files. Voice: 'deselect all'."""
        for cb, var, path in self._checkboxes:
            if path not in self._blocked_files:
                self._schedule(lambda v=var: v.set("0"))

    def set_commit_message(self, msg: str) -> None:
        """Set the commit message. Voice: 'commit message update agent'."""
        if self._commit_entry:
            self._schedule(lambda: self._update_commit_text(msg))

    def confirm(self) -> None:
        """Trigger confirmation. Voice: 'confirm push'."""
        self._schedule(self._on_confirm)

    def cancel(self) -> None:
        """Trigger cancellation. Voice: 'cancel push'."""
        self._schedule(self._on_cancel)

    # --- Window Construction ---

    def _schedule(self, fn) -> None:
        """Thread-safe GUI update via after()."""
        if self._root:
            try:
                self._root.after(0, fn)
            except Exception:
                pass

    def _build_window(self, status: PushStatus, scan: "ScanReport") -> None:
        """Construct the full review window."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self._root = ctk.CTk()
        self._root.title("🔒 SANI — Push Review")
        self._root.geometry("720x680")
        self._root.resizable(True, True)
        self._root.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Bring to front
        self._root.attributes("-topmost", True)
        self._root.after(200, lambda: self._root.attributes("-topmost", False))

        self._blocked_files = scan.blocked_files() if scan else set()

        # --- Header ---
        header = ctk.CTkFrame(self._root, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))

        ctk.CTkLabel(
            header, text="🔒 Push Review", font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")

        # --- Branch / Remote Info ---
        info_frame = ctk.CTkFrame(self._root, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=(5, 10))

        info_texts = [
            f"Branch:  {status.branch} → origin/{status.branch}",
            f"Remote:  {status.remote_url or 'not configured'}",
            f"Commits ahead:  {status.commits_ahead}",
        ]
        for text in info_texts:
            ctk.CTkLabel(info_frame, text=text, font=ctk.CTkFont(size=13), anchor="w").pack(
                fill="x", padx=15, pady=2,
            )

        # --- File Checklist ---
        files_label = ctk.CTkLabel(
            self._root, text="Files to Push", font=ctk.CTkFont(size=15, weight="bold"), anchor="w",
        )
        files_label.pack(fill="x", padx=20, pady=(5, 0))

        files_frame = ctk.CTkScrollableFrame(self._root, corner_radius=10, height=200)
        files_frame.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        files_frame.grid_columnconfigure(0, weight=1)

        warned_files = scan.warned_files() if scan else set()
        self._checkboxes = []

        for i, file_info in enumerate(status.changed_files):
            path = file_info["path"]
            file_status = file_info.get("status", "modified")

            var = ctk.StringVar(value="0")
            is_blocked = path in self._blocked_files
            is_warned = path in warned_files

            # Build label text with badges
            badge = ""
            if is_blocked:
                badge = "  🔴 BLOCKED"
                var.set("0")
            elif is_warned:
                badge = "  🟡 WARNING"
                var.set("0")
            else:
                var.set("1")

            display = f"{path}  ({file_status}){badge}"

            cb = ctk.CTkCheckBox(
                files_frame,
                text=display,
                variable=var,
                onvalue="1",
                offvalue="0",
                font=ctk.CTkFont(size=12),
                text_color="#FF6B6B" if is_blocked else ("#FFD93D" if is_warned else None),
                state="disabled" if is_blocked else "normal",
            )
            cb.grid(row=i, column=0, padx=10, pady=3, sticky="ew")
            self._checkboxes.append((cb, var, path))

        # --- Security Scan Results ---
        if scan and scan.findings:
            scan_label = ctk.CTkLabel(
                self._root, text="Security Scan Results",
                font=ctk.CTkFont(size=15, weight="bold"), anchor="w",
            )
            scan_label.pack(fill="x", padx=20, pady=(5, 0))

            scan_frame = ctk.CTkScrollableFrame(self._root, corner_radius=10, height=100)
            scan_frame.pack(fill="x", padx=20, pady=(5, 10))
            scan_frame.grid_columnconfigure(0, weight=1)

            for j, finding in enumerate(scan.findings):
                icon = "🔴" if finding.severity.value == "CRITICAL" else "🟡"
                loc = f":{finding.line}" if finding.line > 0 else ""
                text = f"{icon} {finding.file}{loc} — {finding.message} ({finding.snippet})"
                ctk.CTkLabel(
                    scan_frame, text=text, font=ctk.CTkFont(size=11), anchor="w",
                    text_color="#FF6B6B" if finding.severity.value == "CRITICAL" else "#FFD93D",
                ).grid(row=j, column=0, padx=10, pady=2, sticky="ew")

        # --- Commit Message ---
        commit_label = ctk.CTkLabel(
            self._root, text="Commit Message", font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        )
        commit_label.pack(fill="x", padx=20, pady=(5, 0))

        self._commit_entry = ctk.CTkTextbox(self._root, height=50, corner_radius=8, font=ctk.CTkFont(size=12))
        self._commit_entry.pack(fill="x", padx=20, pady=(5, 10))

        # Auto-generate default commit message
        selected_count = sum(1 for _, v, p in self._checkboxes if v.get() == "1")
        default_msg = self._auto_commit_message(status.changed_files, selected_count)
        self._commit_entry.insert("1.0", default_msg)

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(self._root, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkButton(
            btn_frame, text="Select All", width=100, fg_color="#3B8ED0",
            command=self.select_all,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="Deselect All", width=100, fg_color="#565B5E",
            command=self.deselect_all,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame, text="❌ Cancel", width=120, fg_color="#D35B58", hover_color="#C74B48",
            command=self._on_cancel,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame, text="✅ Confirm Push", width=150, fg_color="#2FA572", hover_color="#249960",
            command=self._on_confirm, font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="right", padx=5)

    # --- Event Handlers ---

    def _on_confirm(self) -> None:
        selected = [path for _, var, path in self._checkboxes if var.get() == "1"]
        commit_msg = self._commit_entry.get("1.0", "end").strip() if self._commit_entry else ""
        self._decision = PushDecision(cancelled=False, selected_files=selected, commit_message=commit_msg)
        self._result_event.set()
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception:
                pass
            self._root = None

    def _on_cancel(self) -> None:
        self._decision = PushDecision(cancelled=True)
        self._result_event.set()
        if self._root:
            try:
                self._root.quit()
                self._root.destroy()
            except Exception:
                pass
            self._root = None

    def _update_commit_text(self, msg: str) -> None:
        if self._commit_entry:
            self._commit_entry.delete("1.0", "end")
            self._commit_entry.insert("1.0", msg)

    @staticmethod
    def _auto_commit_message(files: list[dict], count: int) -> str:
        """Generate a concise default commit message."""
        if count == 0:
            return "No files selected"
        names = [f["path"].split("/")[-1] for f in files[:5]]
        summary = ", ".join(names)
        if count > 5:
            summary += f" (+{count - 5} more)"
        return f"Update {count} file(s): {summary}"
