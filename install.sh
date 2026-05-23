#!/usr/bin/env bash
#
# logo-finder installer — installs the CLI and the Claude Code skill.
#
#   Local:   ./install.sh
#   Remote:  curl -fsSL https://raw.githubusercontent.com/ernanibmurtinho/colosseum-find-my-logo/main/install.sh | bash
#
# Override the skill location with CLAUDE_SKILLS_DIR (default: ~/.claude/skills).
set -euo pipefail

REPO_URL="https://github.com/ernanibmurtinho/colosseum-find-my-logo.git"
SKILL_NAME="logo-finder"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

say()  { printf '\033[1;32m›\033[0m %s\n' "$1"; }
warn() { printf '\033[1;33m!\033[0m %s\n' "$1"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

is_repo() { [ -f "$1/pyproject.toml" ] && grep -q 'name = "logo-finder"' "$1/pyproject.toml" 2>/dev/null; }

# 1. Locate the repo: a local checkout, the script's own dir, or clone it.
if is_repo "$(pwd)"; then
  REPO_DIR="$(pwd)"
  say "Installing from current checkout: $REPO_DIR"
elif [ -n "${BASH_SOURCE:-}" ] && is_repo "$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo /nonexistent)"; then
  REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  say "Installing from script directory: $REPO_DIR"
else
  command -v git >/dev/null 2>&1 || die "git is required to clone the repo."
  REPO_DIR="${HOME}/.local/share/logo-finder"
  if [ -d "$REPO_DIR/.git" ]; then
    say "Updating existing checkout at $REPO_DIR"
    git -C "$REPO_DIR" pull --ff-only
  else
    say "Cloning $REPO_URL → $REPO_DIR"
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
  fi
fi

# 2. Install the CLI (prefer isolated tools, fall back to pip).
if command -v uv >/dev/null 2>&1; then
  say "Installing the logo-finder CLI with uv"
  uv tool install --force "$REPO_DIR"
elif command -v pipx >/dev/null 2>&1; then
  say "Installing the logo-finder CLI with pipx"
  pipx install --force "$REPO_DIR"
elif command -v pip3 >/dev/null 2>&1; then
  say "Installing the logo-finder CLI with pip"
  pip3 install --user "$REPO_DIR"
elif command -v pip >/dev/null 2>&1; then
  say "Installing the logo-finder CLI with pip"
  pip install --user "$REPO_DIR"
else
  die "Need one of: uv, pipx, or pip to install the CLI."
fi

# 3. Install the Claude skill.
say "Installing the Claude skill → $SKILLS_DIR/$SKILL_NAME"
mkdir -p "$SKILLS_DIR/$SKILL_NAME"
cp -f "$REPO_DIR/skill/$SKILL_NAME/SKILL.md" "$SKILLS_DIR/$SKILL_NAME/SKILL.md"

# 4. Optional dependency for high-quality GIFs.
command -v ffmpeg >/dev/null 2>&1 || \
  warn "ffmpeg not found — MP4 works, but high-quality GIF export needs it (apt install ffmpeg / brew install ffmpeg)."

say "Done."
echo
echo "  In Claude Code:  ask \"find my logo in this mosaic\" (hand it your logo + the mosaic)"
echo "  On the CLI:      logo-finder --help"
echo
warn "If 'logo-finder' isn't found, add your user bin to PATH (e.g. ~/.local/bin)."
