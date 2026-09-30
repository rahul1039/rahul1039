#!/usr/bin/env python3
"""Refresh the AUTO-GENERATED section of the profile README.

Only the text between the START/END markers is rewritten; everything else in
README.md is left untouched. If the markers don't exist yet, a marked section
is appended to the end of the file (nothing existing is modified).

Auth: uses GITHUB_TOKEN if set (built-in Actions token). Works unauthenticated
too, with lower rate limits.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter

API = "https://api.github.com"
START = "<!-- AUTO-GENERATED:START -->"
END = "<!-- AUTO-GENERATED:END -->"
README = os.environ.get("README_PATH", "README.md")
USER = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "rahul1039"
TOP_N = 5


def api_get(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "profile-readme-updater",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code} for {path}: {e.read().decode()[:200]}")


def fetch_repos(user):
    repos, page = [], 1
    while True:
        batch = api_get(f"/users/{user}/repos?type=owner&per_page=100&page={page}")
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def render(profile, repos):
    own = [r for r in repos if not r["fork"] and not r["archived"]
           and r["name"].lower() != USER.lower()]
    stars = sum(r["stargazers_count"] for r in own)
    langs = Counter(r["language"] for r in own if r["language"])
    total = sum(langs.values()) or 1

    top = sorted(own, key=lambda r: (-r["stargazers_count"], -r["forks_count"], r["name"].lower()))[:TOP_N]
    recent = sorted(own, key=lambda r: r["pushed_at"] or "", reverse=True)[:TOP_N]

    def row(r):
        desc = (r["description"] or "").replace("|", "\\|").strip() or "—"
        return f"| [{r['name']}]({r['html_url']}) | {desc} | {r['language'] or '—'} | ⭐ {r['stargazers_count']} |"

    out = ["### 📊 GitHub at a glance", "",
           "| Repos | Stars | Followers | Following |", "|:-:|:-:|:-:|:-:|",
           f"| {profile['public_repos']} | {stars} | {profile['followers']} | {profile['following']} |", ""]
    if langs:
        out += ["**Top languages:** " + " · ".join(
            f"{l} ({c * 100 // total}%)" for l, c in langs.most_common(6)), ""]
    hdr = ["| Repository | Description | Language | Stars |", "|---|---|---|:-:|"]
    if top:
        out += ["#### ⭐ Top repositories", ""] + hdr + [row(r) for r in top] + [""]
    if recent:
        out += ["#### 🕒 Recently active", ""] + hdr + [row(r) for r in recent] + [""]
    return "\n".join(out).rstrip() + "\n"


def splice(text, body):
    block = f"{START}\n{body}{END}"
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pat.search(text):
        return pat.sub(lambda _: block, text)
    return text.rstrip("\n") + "\n\n" + block + "\n"


def main():
    profile = api_get(f"/users/{USER}")
    repos = fetch_repos(USER)
    try:
        with open(README, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        text = ""
    new = splice(text, render(profile, repos))
    if new != text:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(new)
        print("README.md updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
