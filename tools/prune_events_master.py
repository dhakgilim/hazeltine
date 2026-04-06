#!/usr/bin/env python3
"""Drop events that have fully ended (end_date or date before today, America/Chicago)."""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data"
MASTER = DATA / "events-master.json"
BACKUP = DATA / "events-master.backup.json"


def event_end_iso(ev: dict) -> str:
    ed = (ev.get("end_date") or "").strip()[:10]
    d = (ev.get("date") or "").strip()[:10]
    return ed if ed else d


def main() -> None:
    today = datetime.now(ZoneInfo("America/Chicago")).date().isoformat()
    raw = json.loads(MASTER.read_text(encoding="utf-8"))
    events = raw if isinstance(raw, list) else raw.get("events", [])
    if not events:
        raise SystemExit("No events in master file")

    kept = [e for e in events if event_end_iso(e) >= today]
    removed = len(events) - len(kept)

    shutil.copy2(MASTER, BACKUP)
    if isinstance(raw, list):
        out = kept
    else:
        raw = dict(raw)
        raw["events"] = kept
        out = raw

    MASTER.write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Today {today}: kept {len(kept)}, removed {removed} past-ended events. "
        f"Backup → {BACKUP.name}"
    )


if __name__ == "__main__":
    main()
