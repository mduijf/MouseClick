#!/bin/bash
# Draai dit nadat je bent ingelogd met: gh auth login
set -e
cd "$(dirname "$0")"

if ! gh auth status >/dev/null 2>&1; then
  echo "Niet ingelogd. Draai eerst: gh auth login"
  exit 1
fi

REPO_NAME="MouseClick"
if gh repo view "$REPO_NAME" >/dev/null 2>&1; then
  echo "Repo bestaat al, push naar origin..."
  git remote add origin "https://github.com/$(gh api user -q .login)/${REPO_NAME}.git" 2>/dev/null || true
else
  echo "Repo aanmaken op GitHub..."
  gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
  echo ""
  echo "Klaar! Open Actions-tab voor de .exe build:"
  gh repo view --web
  exit 0
fi

git push -u origin main
echo ""
echo "Klaar! Download de .exe via GitHub → Actions → laatste run → Artifacts"
