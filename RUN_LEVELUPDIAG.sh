#!/usr/bin/env sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CAMPAIGN=${1:-standard}
if [ "$#" -gt 0 ]; then shift; fi
exec python3 "$HERE/levelupdiag.py" run "$CAMPAIGN" "$@"
