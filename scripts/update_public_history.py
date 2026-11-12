#!/usr/bin/env python3
"""Generate a public, release-notes-only Oakleaf Android changelog.

The source application repository is PRIVATE. This script reads only this
PUBLIC download repository's already-published GitHub Releases.
"""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

OWNER = "wayneward234-prog"
REPO = "Oakleaf-Library-Downloads"
API = f"https://api.github.com/repos/{OWNER}/{REPO}/releases?per_page=100"
VERSION = re.compile(r"^android-(\d+)\.(\d+)\.(\d+)$")


def main():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Oakleaf-Public-Changelog",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urlopen(Request(API, headers=headers), timeout=25) as response:
        releases = json.load(response)

    def published_with_apk(release):
        return (
            not release.get("draft")
            and release.get("published_at")
            and any(a.get("name") == "Oakleaf-Library.apk"
                    for a in release.get("assets", []))
        )

    releases = [r for r in releases if published_with_apk(r)]
    numeric = sorted(
        (r for r in releases if VERSION.fullmatch(r.get("tag_name", ""))),
        key=lambda r: tuple(map(int, VERSION.fullmatch(r["tag_name"]).groups())),
        reverse=True,
    )
    other = sorted(
        (r for r in releases if not VERSION.fullmatch(r.get("tag_name", ""))),
        key=lambda r: r["published_at"],
        reverse=True,
    )
    lines = [
        "# Oakleaf Library — Public Android Version History",
        "",
        "This public page lists the **published Android APK releases** for Oakleaf Library,",
        "newest version first. Entries reproduce the release notes supplied when each",
        "APK was published; they are **not independent verification** of every claim.",
        "",
        "The application source, development details, private catalogue information",
        "and signing material are **not published here**.",
        "",
        "Download the [latest Android APK](https://github.com/"
        f"{OWNER}/{REPO}/releases/latest/download/Oakleaf-Library.apk).",
        "",
    ]
    def append_release(release, name):
        date = datetime.datetime.fromisoformat(
            release["published_at"].replace("Z", "+00:00")
        ).strftime("%d %B %Y").lstrip("0")
        notes = (release.get("body") or "").replace("\r\n", "\n").strip()
        lines.extend([
            f"## {name} — {date}",
            "",
            f"[View this GitHub release]({release['html_url']})",
            "",
            notes or "_No release description provided._",
            "",
        ])
    for release in numeric:
        append_release(release, "Version " + release["tag_name"].removeprefix("android-"))
    if other:
        lines.extend(["## Other published test APKs", ""])
        for release in other:
            append_release(release, release.get("name") or release["tag_name"])
    Path("CHANGELOG.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
