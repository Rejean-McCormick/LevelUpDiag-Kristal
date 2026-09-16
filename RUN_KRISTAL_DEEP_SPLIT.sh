#!/usr/bin/env sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HERE/scripts/run_deep_split.py" "$@"
