#!/bin/bash
# usage: publish_branch.sh <site dir, a shallow clone of the branch or empty> <new content dir> <branch>
# Replaces the branch with one commit holding the new content; does nothing when the content is unchanged.
set -euo pipefail
site=$1 content=$2 branch=$3

if diff -rq --exclude=.git "$site" "$content" >/dev/null 2>&1; then
  echo "$branch unchanged"
  exit 0
fi

cd "$site"
[ -d .git ] || git init -q
git config user.email "github-action@users.noreply.github.com"
git config user.name "GitHub Action"
# Built in the clone so unchanged blobs (the Tor bundles) are not uploaded again.
git checkout -q --orphan next
git rm -rqf --cached . >/dev/null 2>&1 || true
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$content"/. .
git add -A
git commit -q -m "Update $branch on $(date -u '+%Y-%m-%d %H:%M')"
git push -q -f "https://${GITHUB_ACTOR}:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}" "next:$branch"
echo "$branch published"
