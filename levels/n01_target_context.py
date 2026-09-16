from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from levelupdiag_core.commands import run_command
from levelupdiag_core.vcs import git_info


def run(cfg, report):
    target = Path(cfg["_target_root"])
    tool = Path(cfg["_tool_root"])
    control = Path(cfg["_control_root"])

    report.add(
        "target.root.exists",
        "PASS" if target.is_dir() else "CONFIG_ERROR",
        "target",
        "Target repository root is available.",
        path=str(target),
    )

    separated = tool.resolve() != target.resolve() and not tool.resolve().is_relative_to(target.resolve())
    report.add(
        "target.layout.external_harness",
        "PASS" if separated else "FAIL",
        "target",
        "LevelUpDiag Kristal is external to the target repository."
        if separated
        else "Diagnostics source is inside or identical to the Kristal target; this adaptation requires a separate repository.",
        evidence={"tool_root": str(tool), "target_root": str(target)},
        recommendation=None if separated else "Move the harness to a sibling repository such as C:\\mycode\\Kristal\\levelupdiag_kristal.",
    )

    control_external = control.resolve().is_relative_to(tool.resolve()) and not control.resolve().is_relative_to(target.resolve())
    report.add(
        "target.evidence.external",
        "PASS" if control_external else "FAIL",
        "target",
        "Generated evidence is stored under the external harness repository."
        if control_external
        else "Generated evidence is not isolated from the Kristal target.",
        evidence={"control_root": str(control)},
    )

    report.add(
        "runtime.platform.detected",
        "PASS",
        "environment",
        "Runtime platform detected.",
        evidence={"system": platform.system(), "release": platform.release(), "python": sys.version.split()[0]},
    )

    gi = git_info(target)
    if gi.get("repository"):
        report.add(
            "target.vcs.git.detected",
            "PASS",
            "vcs",
            "Git repository detected.",
            evidence={"head": gi.get("head"), "branch": gi.get("branch"), "tracked_dirty": bool(gi.get("tracked_status"))},
        )
    else:
        report.add(
            "target.vcs.detected",
            "WARN",
            "vcs",
            "No Git repository was detected; VCS protection will be limited.",
            evidence={"git_available": gi.get("available")},
        )

    tool_git = git_info(tool)
    if tool_git.get("repository"):
        rel = control.relative_to(tool).as_posix()
        ignored = run_command(["git", "check-ignore", "-q", "--", rel], cwd=tool, timeout_seconds=10, capture_limit_kb=16)
        report.add(
            "harness.control_dir.ignored",
            "PASS" if ignored["exit_code"] == 0 else "WARN",
            "vcs",
            "Generated harness evidence is ignored by Git."
            if ignored["exit_code"] == 0
            else "Generated harness evidence is not ignored by Git.",
            evidence={"control_dir": rel},
            recommendation=None if ignored["exit_code"] == 0 else f"Add {rel}/ to the harness .gitignore.",
        )

    report.metrics.update({"cwd": os.getcwd(), "control_root": str(control), "git": gi})
