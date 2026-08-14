"""Push Workflow Engine — Orchestrates the full interactive push process.

Connects SecurityScanner, GitTool, PushReviewWindow, and ToolProgressWindow
into a multi-phase workflow: Status → Scan → Review → Confirm → Execute.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from sani.tools.security_scanner import SecurityScanner
from sani.ui.push_review_window import PushDecision, PushReviewWindow, PushStatus
from sani.ui.tool_progress_window import ToolProgressWindow

if TYPE_CHECKING:
    from sani.tools.git_tool import GitTool


class PushWorkflowEngine:
    """Orchestrates the full interactive push workflow with GUI windows."""

    def __init__(self, git_tool: "GitTool", workspace_root: str | Path) -> None:
        self.git_tool = git_tool
        self.workspace_root = str(workspace_root)
        self.scanner = SecurityScanner()

        # Exposed for voice control while review window is open
        self.review_window: PushReviewWindow | None = None
        self.progress_window: ToolProgressWindow | None = None

    def run_interactive(self, headless: bool = False) -> tuple[bool, str]:
        """Run the interactive push workflow. Returns (success, message).

        If headless=True, skips GUI window creation and auto-selects clean files.
        """
        import os
        if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("HEADLESS") == "1":
            headless = True

        # ── Phase 1: Gather Status ──
        print("\n[SANI Push Workflow] Gathering repository status...")
        status = self._gather_status()

        if not status.remote_url:
            return False, "No Git remote configured. Cannot push."

        if not status.changed_files and status.commits_ahead == 0:
            return False, "Everything is already up-to-date. Nothing to push."

        # ── Phase 2: Security Scan ──
        print("[SANI Push Workflow] Running security scan...")
        file_paths = [f["path"] for f in status.changed_files]
        scan_report = self.scanner.scan_workspace(Path(self.workspace_root), file_paths)

        critical = scan_report.critical_count
        warnings = scan_report.warning_count
        print(f"[SANI Push Workflow] Scan complete: {critical} critical, {warnings} warnings, {scan_report.scanned_count} files scanned.")

        if headless:
            blocked = scan_report.blocked_files()
            selected = [f["path"] for f in status.changed_files if f["path"] not in blocked]
            if not selected and status.commits_ahead == 0:
                return False, "Push cancelled: all changed files are blocked by security scanner."
            decision = PushDecision(
                cancelled=False,
                selected_files=selected,
                commit_message=f"Update {len(selected)} file(s)",
            )
        else:
            # ── Phase 3: Open Review Window ──
            print("[SANI Push Workflow] Opening review window...")
            self.review_window = PushReviewWindow()
            self.review_window.open(status, scan_report)
            decision = self.review_window.wait_for_result()
            self.review_window = None

        if decision.cancelled:
            return False, "Push cancelled by user."

        if not decision.selected_files and status.commits_ahead == 0:
            return False, "No files selected. Push cancelled."

        # ── Phase 4: Execute Push ──
        return self._execute_push(decision, status, headless=headless)

    def _execute_push(self, decision: PushDecision, status: PushStatus, headless: bool = False) -> tuple[bool, str]:
        """Stage, commit, and push selected files."""
        if not headless:
            self.progress_window = ToolProgressWindow()
            self.progress_window.open()

            steps = ["Security Scan", "Stage Files", "Commit", "Push"]
            for step in steps:
                self.progress_window.add_step(step)

            time.sleep(0.1)
            self.progress_window.update()

        try:
            # Step 1: Final security re-check on selected files
            if not headless and self.progress_window:
                self.progress_window.start_step("Security Scan", "Verifying selected files...")
                self.progress_window.update()

            if decision.selected_files:
                re_scan = self.scanner.scan_workspace(Path(self.workspace_root), decision.selected_files)
                if re_scan.critical_count > 0:
                    blocked = ", ".join(re_scan.blocked_files())
                    if not headless and self.progress_window:
                        self.progress_window.fail_step("Security Scan", f"Blocked: {blocked}")
                        self.progress_window.update()
                        self.progress_window.close()
                    return False, f"Push blocked: critical security findings in {blocked}"

            if not headless and self.progress_window:
                self.progress_window.complete_step("Security Scan", "files clean")
                self.progress_window.update()

            # Step 2: Stage selected files (only if there are uncommitted files to stage)
            if decision.selected_files:
                if not headless and self.progress_window:
                    self.progress_window.start_step("Stage Files", f"Staging {len(decision.selected_files)} files...")
                    self.progress_window.update()
                ok, stage_msg = self._stage_files(decision.selected_files)
                if not ok:
                    if not headless and self.progress_window:
                        self.progress_window.fail_step("Stage Files", stage_msg)
                        self.progress_window.update()
                        self.progress_window.close()
                    return False, f"Staging failed: {stage_msg}"
                if not headless and self.progress_window:
                    self.progress_window.complete_step("Stage Files", f"{len(decision.selected_files)} files staged")
                    self.progress_window.update()

                # Step 3: Commit
                commit_msg = decision.commit_message or "Update files"
                if not headless and self.progress_window:
                    self.progress_window.start_step("Commit", f"Committing: {commit_msg[:50]}...")
                    self.progress_window.update()
                ok, commit_out = self._commit(commit_msg)
                if not ok:
                    if not headless and self.progress_window:
                        self.progress_window.fail_step("Commit", commit_out)
                        self.progress_window.update()
                        self.progress_window.close()
                    return False, f"Commit failed: {commit_out}"
                if not headless and self.progress_window:
                    self.progress_window.complete_step("Commit", "committed successfully")
                    self.progress_window.update()

            # Step 4: Push
            if not headless and self.progress_window:
                self.progress_window.start_step("Push", f"Pushing to {status.remote_url}...")
                self.progress_window.update()
            ok, push_out = self.git_tool.push(self.workspace_root)
            if not headless and self.progress_window:
                if ok:
                    self.progress_window.complete_step("Push", "pushed successfully")
                else:
                    self.progress_window.fail_step("Push", push_out)
                self.progress_window.update()

                self.progress_window.close()
                time.sleep(1.0)
                self.progress_window.update()
                self.progress_window = None

            return ok, "GitHub push completed." if ok else f"Push failed: {push_out}"

        except Exception as e:
            if not headless and self.progress_window:
                self.progress_window.fail_step("Push", str(e))
                self.progress_window.update()
                self.progress_window.close()
                self.progress_window = None
            return False, f"Push workflow error: {e}"

    # --- Git Operations ---

    def _gather_status(self) -> PushStatus:
        """Collect branch, remote, commits ahead, and changed files."""
        branch = self.git_tool.get_current_branch(self.workspace_root) or "HEAD"
        remote_url = self.git_tool.get_remote_url(self.workspace_root)
        commit_count, unpushed_files = self.git_tool.list_unpushed_files(self.workspace_root)

        # Also get unstaged/untracked files from git status
        ok, status_out = self.git_tool._run_git(["status", "--porcelain"], cwd=self.workspace_root)
        changed_files: list[dict] = []
        seen_paths: set[str] = set()

        if ok and status_out:
            for line in status_out.splitlines():
                if len(line) >= 3:
                    status_code = line[:2]
                    path = line[2:].strip()
                    if not path or path in seen_paths:
                        continue
                    seen_paths.add(path)

                    if status_code == "??":
                        file_status = "untracked"
                    elif "D" in status_code:
                        file_status = "deleted"
                    elif "A" in status_code:
                        file_status = "new"
                    else:
                        file_status = "modified"

                    changed_files.append({"path": path, "status": file_status})

        # Add unpushed committed files not already in working tree changes
        for f in unpushed_files:
            if f not in seen_paths:
                changed_files.append({"path": f, "status": "committed"})
                seen_paths.add(f)

        return PushStatus(
            branch=branch,
            remote_url=remote_url,
            commits_ahead=commit_count,
            changed_files=changed_files,
        )

    def _stage_files(self, files: list[str]) -> tuple[bool, str]:
        """Stage specific files."""
        return self.git_tool._run_git(["add", "--"] + files, cwd=self.workspace_root)

    def _commit(self, message: str) -> tuple[bool, str]:
        """Commit staged files."""
        return self.git_tool._run_git(["commit", "-m", message], cwd=self.workspace_root)
