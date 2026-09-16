#!/usr/bin/env sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$HERE"
python3 -m unittest discover -s tests -v
python3 levelupdiag.py list
python3 levelupdiag.py doctor
