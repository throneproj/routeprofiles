#!/usr/bin/env python3
"""Build Throne's bridges-v1.json from the Tor Project's published bridge configuration.

usage: tor_feed.py <published bridges-v1.json, may be missing> <output path>
Writes nothing when the content matches the published copy.
"""
import datetime
import json
import re
import subprocess
import sys

RDSYS_CONF = "https://gitlab.torproject.org/tpo/anti-censorship/rdsys-admin/-/raw/main/conf/"
TOR_BROWSER_API = "https://gitlab.torproject.org/api/v4/projects/tpo%2Fapplications%2Ftor-browser"
TOR_BROWSER_PREFS = "https://gitlab.torproject.org/tpo/applications/tor-browser/-/raw/{}/browser/app/profile/000-tor-browser.js"
MOAT_URL = "https://bridges.torproject.org/moat"
BUILTIN_TYPES = ("snowflake", "obfs4", "meek")
TRANSPORTS = {"obfs4", "webtunnel", "meek_lite", "snowflake"}
LINE = re.compile(
    r"^(?:(?P<transport>[a-z0-9_]+) )?"
    r"(?:\d{1,3}(?:\.\d{1,3}){3}|\[[0-9a-fA-F:.]+\]):\d{1,5}"
    r"(?: [0-9A-Fa-f]{40})?"
    r"(?: [^\s=]+=\S*)*$"
)
TARGETS = re.compile(r"^https://[^\s|]+\|[^\s|]+$")


def fetch(url):
    # gitlab.torproject.org refuses unfamiliar user agents; curl's passes.
    return subprocess.run(["curl", "-fsSL", "--retry", "3", "--max-time", "60", url], check=True, capture_output=True).stdout


def normalized(line):
    line = " ".join(line.split())
    match = LINE.match(line)
    if not match or (match.group("transport") and match.group("transport") not in TRANSPORTS):
        sys.exit("unexpected bridge line: " + line[:80])
    return line


def unique(lines):
    out = []
    for line in map(normalized, lines):
        if line not in out:
            out.append(line)
    return out


def moat_targets(published):
    try:
        branch = json.loads(fetch(TOR_BROWSER_API))["default_branch"]
        prefs = fetch(TOR_BROWSER_PREFS.format(branch)).decode()
        match = re.search(r'pref\("extensions\.torlauncher\.bridgedb_targets",\s*"([^"]+)"\)', prefs)
        if match and TARGETS.match(match.group(1)):
            return match.group(1)
        print("bridgedb_targets not found on", branch, file=sys.stderr)
    except Exception as error:
        print("Moat front lookup failed:", error, file=sys.stderr)
    if published:
        return published["moat"]["targets"]
    sys.exit("no Moat front")


def main():
    published_path, out_path = sys.argv[1], sys.argv[2]
    published = None
    try:
        with open(published_path, encoding="utf-8") as f:
            published = json.load(f)
    except FileNotFoundError:
        pass

    builtin = json.loads(fetch(RDSYS_CONF + "builtin.json"))
    circumvention = json.loads(fetch(RDSYS_CONF + "circumvention.json"))
    doc = {
        "version": 1,
        "revision": 0,
        "builtin": {kind: unique(builtin.get(kind, [])) for kind in BUILTIN_TYPES},
        "countries": {},
        "moat": {"url": MOAT_URL, "targets": moat_targets(published)},
    }
    for kind, lines in doc["builtin"].items():
        if not lines:
            sys.exit("no built-in " + kind + " bridges")
    for country in sorted(circumvention):
        if not re.fullmatch(r"[a-z]{2}", country):
            continue
        settings = []
        for setting in circumvention[country].get("settings", []):
            bridges = setting.get("bridges", {})
            kind, source = bridges.get("type", ""), bridges.get("source", "")
            # meek-azure is a leftover copy of meek kept for old clients.
            if kind == "meek-azure" or source not in ("builtin", "bridgedb"):
                continue
            entry = {"type": kind, "source": source}
            if bridges.get("bridge_strings"):
                entry["bridges"] = unique(bridges["bridge_strings"])
            settings.append(entry)
        if settings:
            doc["countries"][country] = settings

    if published and {**published, "revision": 0} == doc:
        print("bridges unchanged")
        return
    today = int(datetime.date.today().strftime("%Y%m%d")) * 100 + 1
    doc["revision"] = max(today, published["revision"] + 1 if published else 0)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    print("bridges revision", doc["revision"])


if __name__ == "__main__":
    main()
