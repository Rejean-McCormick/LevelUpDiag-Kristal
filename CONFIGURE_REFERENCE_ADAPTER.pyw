# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import shutil
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent
TARGET = (ROOT.parent / 'kristal-framework').resolve()
REFERENCE = (ROOT.parent / 'kristal-reference').resolve()
LOCAL = ROOT / 'levelupdiag.config.local.json'

ADAPTER = {
    'enabled': True,
    'cwd': '../kristal-reference',
    'commands': {
        'exchange_id': ['node', 'bin/kristal-ref.mjs', 'exchange-id', '{input}'],
        'verify_exchange': ['node', 'bin/kristal-ref.mjs', 'verify-exchange', '{input}'],
        'build_runtime_pack': ['node', 'bin/kristal-ref.mjs', 'build-runtime-pack', '{input}', '{output_dir}'],
        'verify_runtime_pack': ['node', 'bin/kristal-ref.mjs', 'verify-runtime-pack', '{manifest}', '{payload_dir}'],
        'verify_runtime_profiles': ['node', 'bin/kristal-ref.mjs', 'verify-runtime-profile', '{vectors}'],
        'verify_signature': ['node', 'bin/kristal-ref.mjs', 'verify-signature', '{fixture}'],
        'verify_trust': ['node', 'bin/kristal-ref.mjs', 'verify-trust', '{fixture}'],
    },
}


def configure():
    if not (TARGET / 'tools' / 'validate_all.py').exists():
        messagebox.showerror('Kristal Reference Adapter', f'Kristal framework not found:\n{TARGET}')
        return
    if not (REFERENCE / 'bin' / 'kristal-ref.mjs').exists():
        messagebox.showerror('Kristal Reference Adapter', f'kristal-reference not found:\n{REFERENCE}')
        return
    data = {}
    if LOCAL.exists():
        try:
            data = json.loads(LOCAL.read_text(encoding='utf-8'))
        except Exception as exc:
            messagebox.showerror('Kristal Reference Adapter', f'Existing local config is invalid JSON:\n{exc}')
            return
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        shutil.copy2(LOCAL, LOCAL.with_name(f'{LOCAL.name}.backup-{stamp}'))
    data['target_repo_root'] = str(TARGET).replace('\\', '/')
    data['implementation_adapter'] = ADAPTER
    LOCAL.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    messagebox.showinfo('Kristal Reference Adapter', f'Adapter enabled.\n\n{LOCAL}')
    refresh()


def refresh():
    target_var.set(f"Kristal framework: {'OK' if (TARGET / 'tools' / 'validate_all.py').exists() else 'NOT FOUND'} — {TARGET}")
    ref_var.set(f"kristal-reference: {'OK' if (REFERENCE / 'bin' / 'kristal-ref.mjs').exists() else 'NOT FOUND'} — {REFERENCE}")
    cfg_var.set(f"Local config: {'PRESENT' if LOCAL.exists() else 'NOT CREATED'} — {LOCAL}")

app = tk.Tk()
app.title('Configure Kristal Reference Adapter')
app.geometry('820x260')
app.resizable(True, False)
frame = ttk.Frame(app, padding=16)
frame.pack(fill='both', expand=True)
target_var = tk.StringVar(); ref_var = tk.StringVar(); cfg_var = tk.StringVar()
for var in (target_var, ref_var, cfg_var):
    ttk.Label(frame, textvariable=var, wraplength=770).pack(anchor='w', pady=5)
ttk.Separator(frame).pack(fill='x', pady=10)
ttk.Button(frame, text='Enable / Update Reference Adapter', command=configure).pack(pady=8)
ttk.Label(frame, text='Existing local config is backed up before modification. Only target_repo_root and implementation_adapter are updated.', wraplength=770).pack(anchor='w', pady=5)
refresh()
app.mainloop()
