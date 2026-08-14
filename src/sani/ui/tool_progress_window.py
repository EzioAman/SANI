"""Live Tool Progress Window — Auto-updating GUI panel showing real-time execution status.

Displays a step-by-step progress view with status icons, timing, and a progress bar.
Updates are thread-safe via after() scheduling.
"""

from __future__ import annotations

import threading
import time

import customtkinter as ctk


class ToolProgressWindow:
    """CustomTkinter GUI showing real-time tool execution progress.

    Thread-safety: Call add_step/start_step/complete_step/fail_step from any thread.
    """

    def __init__(self) -> None:
        self._root: ctk.CTkToplevel | ctk.CTk | None = None
        self._steps: dict[str, dict] = {}
        self._step_labels: dict[str, ctk.CTkLabel] = {}
        self._step_detail_labels: dict[str, ctk.CTkLabel] = {}
        self._progress_bar: ctk.CTkProgressBar | None = None
        self._status_label: ctk.CTkLabel | None = None
        self._steps_frame: ctk.CTkFrame | None = None
        self._step_order: list[str] = []
        self._closed = threading.Event()
        self._total_steps = 0
        self._completed_steps = 0

    def open(self, parent: ctk.CTk | None = None) -> None:
        """Build and show the progress window."""
        ctk.set_appearance_mode("dark")

        if parent:
            self._root = ctk.CTkToplevel(parent)
        else:
            self._root = ctk.CTk()

        self._root.title("⚙ SANI — Push in Progress")
        self._root.geometry("550x380")
        self._root.resizable(True, True)
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent manual close during operation

        # Bring to front
        self._root.attributes("-topmost", True)
        self._root.after(200, lambda: self._root.attributes("-topmost", False))

        # --- Header ---
        header = ctk.CTkFrame(self._root, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            header, text="⚙ Push in Progress",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w")

        # --- Steps Frame ---
        self._steps_frame = ctk.CTkFrame(self._root, corner_radius=10)
        self._steps_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # --- Progress Bar ---
        self._progress_bar = ctk.CTkProgressBar(self._root, width=400, height=16, corner_radius=8)
        self._progress_bar.pack(padx=20, pady=(5, 5))
        self._progress_bar.set(0)

        # --- Status Label ---
        self._status_label = ctk.CTkLabel(
            self._root, text="Initializing...",
            font=ctk.CTkFont(size=13), text_color="#A0A0A0", anchor="w",
        )
        self._status_label.pack(fill="x", padx=20, pady=(0, 15))

    def add_step(self, name: str) -> None:
        """Register a new step. Call before starting execution."""
        self._steps[name] = {"status": "waiting", "detail": "", "start_time": None}
        self._step_order.append(name)
        self._total_steps += 1
        self._schedule(lambda: self._render_step(name))

    def start_step(self, name: str, detail: str = "") -> None:
        """Mark step as in-progress."""
        if name in self._steps:
            self._steps[name]["status"] = "running"
            self._steps[name]["detail"] = detail
            self._steps[name]["start_time"] = time.time()
            self._schedule(lambda: self._update_step_display(name))
            self._schedule(lambda: self._set_status(f"Running: {name}... {detail}"))

    def complete_step(self, name: str, detail: str = "") -> None:
        """Mark step as completed."""
        if name in self._steps:
            elapsed = ""
            if self._steps[name]["start_time"]:
                elapsed = f" ({time.time() - self._steps[name]['start_time']:.1f}s)"
            self._steps[name]["status"] = "done"
            self._steps[name]["detail"] = f"{detail}{elapsed}"
            self._completed_steps += 1
            self._schedule(lambda: self._update_step_display(name))
            self._schedule(self._update_progress)

    def fail_step(self, name: str, error: str = "") -> None:
        """Mark step as failed."""
        if name in self._steps:
            self._steps[name]["status"] = "failed"
            self._steps[name]["detail"] = error
            self._schedule(lambda: self._update_step_display(name))
            self._schedule(lambda: self._set_status(f"❌ Failed: {name} — {error}"))

    def close(self, auto_delay: float = 2.5) -> None:
        """Close the window after a delay (for success) or immediately (for failure)."""
        has_failure = any(s["status"] == "failed" for s in self._steps.values())
        if has_failure:
            # Keep window open and enable close button
            self._schedule(lambda: self._enable_close())
        else:
            self._schedule(lambda: self._set_status("✅ All steps completed successfully!"))
            self._schedule(lambda: self._root.after(int(auto_delay * 1000), self._destroy))

    def run_mainloop(self) -> None:
        """Run the tkinter mainloop (call from main thread if needed)."""
        if self._root:
            self._root.mainloop()

    def update(self) -> None:
        """Process pending GUI events without blocking (for integration with voice pipeline)."""
        if self._root:
            try:
                self._root.update()
            except Exception:
                pass

    # --- Internal Rendering ---

    def _schedule(self, fn) -> None:
        if self._root:
            try:
                self._root.after(0, fn)
            except Exception:
                pass

    def _render_step(self, name: str) -> None:
        """Add a step row to the steps frame."""
        if not self._steps_frame:
            return
        idx = self._step_order.index(name)

        icon_label = ctk.CTkLabel(
            self._steps_frame, text="⬜", font=ctk.CTkFont(size=14), width=30,
        )
        icon_label.grid(row=idx, column=0, padx=(10, 5), pady=4, sticky="w")

        name_label = ctk.CTkLabel(
            self._steps_frame, text=name, font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", width=180,
        )
        name_label.grid(row=idx, column=1, padx=5, pady=4, sticky="w")

        detail_label = ctk.CTkLabel(
            self._steps_frame, text="waiting",
            font=ctk.CTkFont(size=12), text_color="#888888", anchor="w",
        )
        detail_label.grid(row=idx, column=2, padx=5, pady=4, sticky="w")

        self._step_labels[name] = icon_label
        self._step_detail_labels[name] = detail_label

    def _update_step_display(self, name: str) -> None:
        """Update the icon and detail text for a step."""
        step = self._steps.get(name)
        if not step:
            return
        icon_label = self._step_labels.get(name)
        detail_label = self._step_detail_labels.get(name)
        if not icon_label or not detail_label:
            return

        status = step["status"]
        icons = {"waiting": "⬜", "running": "🔄", "done": "✅", "failed": "❌"}
        colors = {"waiting": "#888888", "running": "#3B8ED0", "done": "#2FA572", "failed": "#FF6B6B"}

        icon_label.configure(text=icons.get(status, "⬜"))
        detail_label.configure(text=step["detail"] or status, text_color=colors.get(status, "#888888"))

    def _update_progress(self) -> None:
        if self._progress_bar and self._total_steps > 0:
            self._progress_bar.set(self._completed_steps / self._total_steps)

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.configure(text=text)

    def _enable_close(self) -> None:
        if self._root:
            self._root.protocol("WM_DELETE_WINDOW", self._destroy)
            self._set_status("❌ Push failed. Close window to continue.")

    def _destroy(self) -> None:
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
            self._root = None
            self._closed.set()
