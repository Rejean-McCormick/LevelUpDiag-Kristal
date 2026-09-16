# -*- coding: utf-8 -*-
"""LevelUpDiag Kristal GUI launcher.

Place this file at:
    C:\\mycode\\Kristal\\levelupdiag_kristal\\LEVELUPDIAG_KRISTAL_LAUNCHER.pyw

It expects kristal-framework to be the sibling directory by default.
"""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "LevelUpDiag Kristal Launcher"
ROOT = Path(__file__).resolve().parent
DEFAULT_TARGET = (ROOT.parent / "kristal-framework").resolve()
EVIDENCE_DIR = ROOT / ".levelupdiag"
REQUIREMENTS = ROOT / "requirements-dev.txt"


class Launcher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("980x680")
        self.minsize(820, 560)

        self.proc: subprocess.Popen | None = None
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.target_var = tk.StringVar(value=str(DEFAULT_TARGET))
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.after(100, self._poll_events)
        self._refresh_state()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)
        ttk.Label(top, text="Kristal target:").grid(row=0, column=0, sticky="w")
        self.target_entry = ttk.Entry(top, textvariable=self.target_var)
        self.target_entry.grid(row=0, column=1, sticky="ew", padx=(8, 6))
        ttk.Button(top, text="Browse…", command=self._browse_target).grid(row=0, column=2)
        top.columnconfigure(1, weight=1)

        info = ttk.Frame(self)
        info.pack(fill="x", padx=10, pady=(0, 6))
        self.repo_label = ttk.Label(info, text="")
        self.repo_label.pack(anchor="w")
        self.req_label = ttk.Label(info, text="")
        self.req_label.pack(anchor="w")
        ttk.Label(info, text=f"Evidence: {EVIDENCE_DIR}").pack(anchor="w")

        actions = ttk.LabelFrame(self, text="Actions")
        actions.pack(fill="x", padx=10, pady=6)

        self.install_btn = ttk.Button(actions, text="Install / Update Dependencies", command=self._install_dependencies)
        self.deep_split_btn = ttk.Button(actions, text="Run Deep Split", command=self._run_deep_split)
        self.deep_btn = ttk.Button(actions, text="Run Deep", command=self._run_deep)
        self.stop_btn = ttk.Button(actions, text="Stop", command=self._stop_process, state="disabled")
        self.open_evidence_btn = ttk.Button(actions, text="Open Evidence Folder", command=self._open_evidence)
        self.open_repo_btn = ttk.Button(actions, text="Open Kristal Repo", command=self._open_target)
        self.clear_btn = ttk.Button(actions, text="Clear Output", command=self._clear_output)
        self.refresh_btn = ttk.Button(actions, text="Refresh", command=self._refresh_state)

        buttons = [
            self.install_btn, self.deep_split_btn, self.deep_btn, self.stop_btn,
            self.open_evidence_btn, self.open_repo_btn, self.clear_btn, self.refresh_btn,
        ]
        for i, btn in enumerate(buttons):
            btn.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="ew")
        for col in range(4):
            actions.columnconfigure(col, weight=1)

        output_box = ttk.LabelFrame(self, text="Output")
        output_box.pack(fill="both", expand=True, padx=10, pady=6)
        self.output = tk.Text(output_box, wrap="word", font=("Consolas", 10), undo=False)
        scroll = ttk.Scrollbar(output_box, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        status = ttk.Frame(self)
        status.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Label(status, textvariable=self.status_var).pack(side="left")

    def _browse_target(self) -> None:
        initial = self.target_var.get().strip() or str(ROOT.parent)
        selected = filedialog.askdirectory(
            title="Select kristal-framework repository",
            initialdir=initial if Path(initial).exists() else str(ROOT.parent),
        )
        if selected:
            self.target_var.set(selected)
            self._refresh_state()

    def _target(self) -> Path:
        return Path(self.target_var.get().strip()).expanduser().resolve()

    def _refresh_state(self) -> None:
        target = self._target()
        valid_repo = target.is_dir() and (target / "tools" / "validate_release.py").is_file()
        req_ok = REQUIREMENTS.is_file()
        self.repo_label.config(text=f"Kristal repo: {'OK' if valid_repo else 'NOT FOUND / INVALID'} — {target}")
        self.req_label.config(text=f"requirements-dev.txt: {'OK' if req_ok else 'NOT FOUND'} — {REQUIREMENTS}")
        runnable = valid_repo and self.proc is None
        self.deep_split_btn.config(state="normal" if runnable else "disabled")
        self.deep_btn.config(state="normal" if runnable else "disabled")
        self.install_btn.config(state="normal" if req_ok and self.proc is None else "disabled")

    def _run_python_entry(self, entry: Path, args: list[str], label: str) -> None:
        if not entry.is_file():
            messagebox.showerror(APP_TITLE, f"Missing entry point:\n{entry}")
            return

        target = self._target()
        if not (target / "tools" / "validate_release.py").is_file():
            messagebox.showerror(APP_TITLE, f"Invalid Kristal repository:\n{target}")
            return

        env = os.environ.copy()
        env["KRISTAL_TARGET"] = str(target)
        env["LEVELUPDIAG_TARGET"] = str(target)
        env["LEVELUPDIAG_EVIDENCE_DIR"] = str(EVIDENCE_DIR)
        env["PYTHONUNBUFFERED"] = "1"

        command = [sys.executable, str(entry), *args]
        self._start_process(command, env, label)

    def _run_deep_split(self) -> None:
        target = self._target()
        self._run_python_entry(
            ROOT / "scripts" / "run_deep_split.py",
            ["--target", str(target)],
            "Kristal Deep Split",
        )

    def _run_deep(self) -> None:
        target = self._target()
        self._run_python_entry(
            ROOT / "levelupdiag.py",
            ["--target", str(target), "run", "deep"],
            "Kristal Deep",
        )

    def _install_dependencies(self) -> None:
        if not REQUIREMENTS.is_file():
            messagebox.showerror(APP_TITLE, f"Missing:\n{REQUIREMENTS}")
            return
        self._start_process(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            {**os.environ.copy(), "PYTHONUNBUFFERED": "1"},
            "pip install",
        )

    def _hidden_process_options(self) -> dict:
        """Return Windows process options that prevent console-window flashes."""
        if os.name != "nt":
            return {}

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)

        return {
            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
            "startupinfo": startupinfo,
        }

    def _start_process(self, command: list[str], env: dict[str, str], label: str) -> None:
        if self.proc is not None:
            messagebox.showwarning(APP_TITLE, "A process is already running.")
            return

        self._append(f"\n=== {label} ===\n")
        self._append("$ " + subprocess.list2cmdline(command) + "\n\n")
        self.status_var.set(f"Running: {label}")

        try:
            self.proc = subprocess.Popen(
                command,
                cwd=str(ROOT),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                **self._hidden_process_options(),
            )
        except Exception as exc:
            self.proc = None
            self.status_var.set("Failed to start")
            messagebox.showerror(APP_TITLE, str(exc))
            self._refresh_state()
            return

        self.stop_btn.config(state="normal")
        self._set_action_state(False)
        threading.Thread(target=self._reader_thread, args=(self.proc, label), daemon=True).start()

    def _reader_thread(self, proc: subprocess.Popen, label: str) -> None:
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                self.events.put(("output", line))
            self.events.put(("done", f"{label}|{proc.wait()}"))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "output":
                    self._append(payload)
                elif kind == "done":
                    label, rc_text = payload.rsplit("|", 1)
                    rc = int(rc_text)
                    self._append(f"\n=== Finished: {label} — exit code {rc} ===\n")
                    verdict = None
                    summary_path = EVIDENCE_DIR / "latest" / "summary.json"
                    try:
                        import json
                        if summary_path.is_file():
                            verdict = json.loads(summary_path.read_text(encoding="utf-8")).get("verdict")
                    except Exception:
                        verdict = None
                    shown = verdict or ("PASS" if rc == 0 else f"EXIT {rc}")
                    self.status_var.set(f"Finished: {label} — {shown}")
                    if verdict:
                        self._append(f"Overall verdict: {verdict}\n")
                    self.proc = None
                    self.stop_btn.config(state="disabled")
                    self._set_action_state(True)
                    self._refresh_state()
                elif kind == "error":
                    self._append(f"\n[launcher error] {payload}\n")
                    self.status_var.set("Launcher error")
                    self.proc = None
                    self.stop_btn.config(state="disabled")
                    self._set_action_state(True)
                    self._refresh_state()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_events)

    def _set_action_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.install_btn.config(state=state)
        self.deep_split_btn.config(state=state)
        self.deep_btn.config(state=state)
        self.refresh_btn.config(state=state)
        self.target_entry.config(state=state)

    def _stop_process(self) -> None:
        if self.proc is None:
            return
        if not messagebox.askyesno(APP_TITLE, "Stop the running validation process?"):
            return
        try:
            self.proc.terminate()
            self.status_var.set("Stopping…")
            self._append("\n[launcher] Termination requested.\n")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not stop process:\n{exc}")

    def _open_evidence(self) -> None:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(EVIDENCE_DIR))

    def _open_target(self) -> None:
        target = self._target()
        if target.exists():
            os.startfile(str(target))
        else:
            messagebox.showerror(APP_TITLE, f"Target does not exist:\n{target}")

    def _clear_output(self) -> None:
        self.output.delete("1.0", "end")

    def _append(self, text: str) -> None:
        self.output.insert("end", text)
        self.output.see("end")
        self.update_idletasks()

    def on_close(self) -> None:
        if self.proc is not None and not messagebox.askyesno(
            APP_TITLE, "A validation process is still running.\nClose the launcher anyway?"
        ):
            return
        self.destroy()


if __name__ == "__main__":
    app = Launcher()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
