#!/usr/bin/env bash
# Validate entry: detect Python then run structural + acceptance checks.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYEX=""
for c in python3 python py; do
  if command -v "$c" >/dev/null 2>&1; then
    [ "$c" = "py" ] && PYEX="$c -3" || PYEX="$c"
    break
  fi
done
if [ -z "$PYEX" ]; then
  echo "[ERR] No Python runtime detected. Domain scripts do not require Python;" >&2
  echo "[ERR] only the meta validators validate.py / validate_acceptance.py do." >&2
  exit 2
fi
# shellcheck disable=SC2086
$PYEX -X utf8 "$ROOT/scripts/validate.py" "$ROOT" || exit 1
# shellcheck disable=SC2086
$PYEX -X utf8 "$ROOT/scripts/validate_acceptance.py" "$ROOT" || exit 1
echo "[OK] All validations passed."
