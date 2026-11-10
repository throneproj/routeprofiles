# Service check definitions

`checks-v1.json` tells Throne's Service Check which services to probe through a profile and how to read
their answers. Throne fetches it at most once a day, only when the user starts a check, and uses it only
when it parses and its `revision` is higher than the copy built into the app.

Rules the core enforces (a file breaking any of them is ignored, never half-used):

- `version` must be 1. Unknown keys are rejected, so a new key needs a new version and a new file
  (`checks-v2.json`); keep this one updated for older apps.
- Bump `revision` (YYYYMMDDNN) on every change.
- Requests: `https`, port 443, public host names only; `GET`/`HEAD`; at most 4 per check; bodies are
  capped by `max_body` (default 256 KiB, max 2 MiB); redirects (≤ 5) must obey the same limits.
- Patterns are Go RE2. Rules are tried in order, the first whose conditions all hold decides; a known
  region in `deny_regions` (or outside `allow_regions`) turns any result into `restricted`.
- Results: `available`, `partial`, `restricted`, `blocked`, `unknown`, `failed`.

Before publishing, run the file against the live services from a Throne checkout:

    cd core
    SERVICECHECK_FILE=/path/to/checks-v1.json go test -tags servicecheck_live,with_utls,badlinkname,tfogo_checklinkname0 \
        -ldflags=-checklinkname=0 -run Live -v ./internal/servicecheck/
