#!/usr/bin/env python3
"""
Keep the RECENT WORK / RECENTLY PUSHED block in README.md in sync with GitHub.

Runs daily via GitHub Actions (.github/workflows/update-readme.yml) or locally.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

START = "<!-- RECENT-PROJECTS:START -->"
END = "<!-- RECENT-PROJECTS:END -->"

# Repositories to hide from the table (e.g. fork or profile readme repo).
EXCLUDE = {"arpit797"}

# Prettier project titles for the table.
NAME_OVERRIDES = {
    "Major-Project": "Wanderlust",
    "react-major-project": "React Web App",
    "simonGame": "Simon Memory Game",
    "DSA": "Data Structures & Algorithms",
    "assigment": "Web Dev Assignments",
}

# Fallback descriptions when repo description is empty.
DESC_FALLBACK = {
    "Major-Project": "Full-stack vacation rental & booking platform inspired by Airbnb with auth, reviews and listings",
    "react-major-project": "Interactive and responsive modern React application featuring state management and component architecture",
    "simonGame": "Classic Simon memory game built with JavaScript, dynamic animations, audio feedback, and score tracking",
    "DSA": "Collection of core data structures and algorithmic problem solutions in C++ & JavaScript",
    "assigment": "Frontend and backend development assignments, responsive layouts, and modern web experiments",
}

# Language -> shields.io colour.
LANG_COLOUR = {
    "JavaScript": "F7DF1E",
    "TypeScript": "3178C6",
    "HTML": "E34F26",
    "CSS": "1572B6",
    "C++": "00599C",
    "Java": "ED8B00",
    "Python": "3776AB",
}


def fetch(url: str) -> list | dict:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-updater",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def pretty(name: str) -> str:
    if name in NAME_OVERRIDES:
        return NAME_OVERRIDES[name]
    cleaned = name.rstrip("-").replace("_", "-")
    words = [w for w in cleaned.split("-") if w]
    if len(words) > 4:
        words = words[:4]
    return " ".join(w if w.isupper() else w.capitalize() for w in words)


def build_rows(repos: list[dict], count: int) -> str:
    live = [r for r in repos
            if not r.get("fork") and not r.get("archived") and r.get("name") not in EXCLUDE]
    live.sort(key=lambda r: r.get("pushed_at", ""), reverse=True)
    chosen = live[:count]

    if not chosen:
        return '<p align="center"><sub>No public repositories yet.</sub></p>'

    lines = [
        '<table align="center">',
        '<tr><th align="left">Project</th><th align="left">What it is</th>'
        '<th align="left">Stack</th><th align="left">Updated</th></tr>',
    ]
    for repo in chosen:
        name = pretty(repo["name"])
        url = repo["html_url"]
        desc = (repo.get("description")
                or DESC_FALLBACK.get(repo["name"])
                or "—").strip()
        if len(desc) > 90:
            desc = desc[:87].rstrip() + "…"
        desc = desc.replace("|", "\\|")

        language = repo.get("language")
        if language:
            colour = LANG_COLOUR.get(language, "64748B")
            badge_label = language.replace("-", "--").replace("_", "__").replace(" ", "%20")
            badge_label = badge_label.replace("+", "%2B")
            stack = (f'<img src="https://img.shields.io/badge/{badge_label}-{colour}'
                     f'?style=flat-square&logoColor=white" alt="{language}"/>')
        else:
            stack = "—"

        demo = ""
        if repo.get("homepage"):
            demo = f' · <a href="{repo["homepage"]}">live</a>'

        updated = repo.get("pushed_at", "")[:10]
        lines.append(
            f'<tr><td><a href="{url}"><b>{name}</b></a>{demo}</td>'
            f"<td>{desc}</td><td>{stack}</td><td><sub>{updated}</sub></td></tr>"
        )
    lines.append("</table>")
    return "\n".join(lines)


def splice(text: str, block: str) -> str:
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END), re.DOTALL
    )
    replacement = (
        f"{START}\n<!-- This block is generated. Do not edit by hand. -->\n"
        f"{block}\n{END}"
    )
    updated, n = pattern.subn(lambda _: replacement, text)
    if n == 0:
        raise SystemExit(
            f"Markers not found in {README.name}. Expected {START} ... {END}."
        )
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=os.environ.get("GH_USER", "arpit797"))
    parser.add_argument("--count", type=int, default=6)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if the README would change, without writing")
    args = parser.parse_args()

    try:
        repos = fetch(
            f"https://api.github.com/users/{args.user}/repos"
            "?per_page=100&sort=pushed"
        )
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        print(f"Could not reach the GitHub API: {error}", file=sys.stderr)
        return 1

    if not isinstance(repos, list):
        print(f"Unexpected API response: {repos}", file=sys.stderr)
        return 1

    original = README.read_text(encoding="utf-8")
    updated = splice(original, build_rows(repos, args.count))

    if updated == original:
        print("README already up to date.")
        return 0

    if args.check:
        print("README is out of date.")
        return 1

    README.write_text(updated, encoding="utf-8")
    print(f"README updated with {min(args.count, len(repos))} projects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
