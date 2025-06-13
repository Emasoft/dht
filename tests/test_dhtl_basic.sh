#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$( cd -- "$( dirname "${BASH_SOURCE[0]}" )/../.." &>/dev/null && pwd )"
OUT="$("$ROOT_DIR/dhtl.sh" --no-guardian --quiet version)"
echo "$OUT" | grep -q "Development Helper Toolkit Launcher"
echo "✔ dhtl version OK"
