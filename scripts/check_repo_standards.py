"""Lightweight standard-library-only repo badge/document validation."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = (
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "RELEASES.md",
    "SECURITY.md", "docs/BACKLOG.md", "docs/SPRINTS.md",
)
ERRORS = []

for doc in DOCS:
    if not (ROOT / doc).is_file():
        ERRORS.append(f"Missing required documentation: {doc}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
lines = readme.splitlines()
if not lines or not lines[0].startswith("# "):
    ERRORS.append("README must begin with a project H1")
start = "<!-- madmallard-badges:start -->"
end = "<!-- madmallard-badges:end -->"
if readme.count(start) != 1 or readme.count(end) != 1:
    ERRORS.append("README must have exactly one bounded badge block")
elif readme.index(start) > readme.index(end):
    ERRORS.append("Badge markers are reversed")
else:
    prefix = readme[:readme.index(start)]
    if prefix.strip() != lines[0].strip():
        ERRORS.append("Badges must sit directly under README H1")
    badges = readme[readme.index(start):readme.index(end)]
    for workflow in ("django-ci.yml", "codeql.yml"):
        path = ROOT / ".github" / "workflows" / workflow
        if not path.is_file():
            ERRORS.append(f"Missing workflow: {workflow}")
        url = f"https://github.com/drakeg/tickets/actions/workflows/{workflow}/badge.svg"
        if url not in badges:
            ERRORS.append(f"Missing live workflow badge: {workflow}")
    for label, url in (
        ("issues", "https://img.shields.io/github/issues/drakeg/tickets"),
        ("PRs", "https://img.shields.io/github/issues-pr/drakeg/tickets"),
    ):
        if url not in badges:
            ERRORS.append(f"Missing dynamic {label} badge")
    if "github/license/" in badges and not any(
        (ROOT / name).is_file() for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")
    ):
        ERRORS.append("License badge present without a tracked project license")

if ERRORS:
    for message in ERRORS:
        print("ERROR:", message, file=sys.stderr)
    sys.exit(1)
print("Repository docs and badge structure verified")
