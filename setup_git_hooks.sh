#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

git config core.hooksPath .githooks
hooks_path="$(git config --get core.hooksPath || true)"

if [ "$hooks_path" = ".githooks" ]; then
  echo "Git hooks activated: $hooks_path"
  exit 0
fi

echo "Failed to activate git hooks. Current core.hooksPath: '$hooks_path'" >&2
exit 1
