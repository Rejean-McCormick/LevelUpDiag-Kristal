from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Kristal deep diagnostics as isolated LevelUpDiag selections.")
    ap.add_argument("--target", help="Kristal repository path; default comes from levelupdiag.config.json")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    selections = ["baseline", "N05"] + [f"K{i}" for i in range(10, 19)]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = root / ".levelupdiag" / "split-runs" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    overall = 0
    for selection in selections:
        cmd = [sys.executable, str(root / "levelupdiag.py")]
        if args.target:
            cmd += ["--target", args.target]
        cmd += ["run", selection]
        cp = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        (out_dir / f"{selection}.log").write_text(cp.stdout, encoding="utf-8")
        rows.append({"selection": selection, "exit_code": cp.returncode})
        print(f"{selection:>8}: exit={cp.returncode}")
        if cp.returncode != 0 and overall == 0:
            overall = cp.returncode

    summary = {
        "schema": "levelupdiag-kristal.split-summary.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": args.target,
        "selections": rows,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Split evidence: {out_dir}")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
