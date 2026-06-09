#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="developer-framework-ander-fernandez"
DESCRIPTION="Ander Fernández's AI-assisted software development operating system: agents, skills, reusable app starter, token optimization and product-to-code workflow."

git init
git branch -M main
git add .
git commit -m "chore: publish developer framework"

gh repo create "mazapander/${REPO_NAME}" \
  --public \
  --description "${DESCRIPTION}" \
  --source=. \
  --remote=origin \
  --push

echo "Repository created: https://github.com/mazapander/${REPO_NAME}"
