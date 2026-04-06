#!/usr/bin/env python3
"""
Rewrite static HTML inside index.html #areas-grid and #service-areas-grid-rotated
to match the inline JS city rotation (seed = Chicago day-of-year, same LCG shuffle).

Keeps crawlers / no-JS first paint aligned with the live rotation script.
Run from Hazeltine cron after event/city page refresh.
"""
from __future__ import annotations

import ast
import re
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "index.html"

PINNED_SLUGS = ("minneapolis", "st-paul", "bloomington", "eagan")
GRID_SLOTS = 8
POP_SLOTS = 12


def extract_city_rotation_data(html: str) -> list:
    m = re.search(r"var CITY_ROTATION_DATA = (\[\[.+?\]\]);", html, re.DOTALL)
    if not m:
        raise SystemExit("CITY_ROTATION_DATA not found in index.html")
    return ast.literal_eval(m.group(1))


def seeded_shuffle(arr: list, seed: int) -> list:
    """Match index.html seededShuffle (LCG 16807 mod 2^31-1)."""
    a = list(arr)
    s = int(seed)
    for i in range(len(a) - 1, 0, -1):
        s = (s * 16807 + 0) % 2147483647
        j = s % (i + 1)
        a[i], a[j] = a[j], a[i]
    return a


def day_of_year_chicago() -> int:
    return datetime.now(ZoneInfo("America/Chicago")).timetuple().tm_yday


def render_area_card(c: list) -> str:
    name, slug = c[0], c[1]
    ne = escape(str(name))
    return (
        f'<a href="auto-detailing-{slug}.html" class="area-card"><h3>{ne}</h3>'
        '<span>Mobile service area</span>'
        '<div class="price">Detailing from $149+</div></a>'
    )


def render_pop_link(c: list) -> str:
    name, slug = c[0], c[1]
    ne = escape(str(name))
    return f'<a href="auto-detailing-{slug}.html">{ne}</a>'


def main() -> None:
    html = INDEX.read_text(encoding="utf-8")
    all_cities = extract_city_rotation_data(html)
    pin_set = set(PINNED_SLUGS)
    pinned = [c for c in all_cities if c[1] in pin_set]
    rest = [c for c in all_cities if c[1] not in pin_set]
    seed = day_of_year_chicago()
    shuffled = seeded_shuffle(rest, seed)

    area_cities = pinned + shuffled[: GRID_SLOTS - len(pinned)]
    need_pop = POP_SLOTS - len(pinned)
    skip = GRID_SLOTS - len(pinned)
    pop_rest = shuffled[skip : skip + need_pop]
    i = 0
    while len(pop_rest) < need_pop and shuffled:
        pop_rest.append(shuffled[i % len(shuffled)])
        i += 1
    pop_cities = pinned + pop_rest

    area_inner = (
        "\n      <!-- Synced by tools/update_index_area_lists.py (America/Chicago DOY) -->\n      "
        + "\n      ".join(render_area_card(c) for c in area_cities)
        + "\n    "
    )
    pop_inner = (
        "\n    <!-- Synced by tools/update_index_area_lists.py -->\n    "
        + "\n    ".join(render_pop_link(c) for c in pop_cities)
        + "\n  "
    )

    html, n1 = re.subn(
        r'(<div class="areas-grid" id="areas-grid">\s*)[\s\S]*?(\s*</div>\s*<div class="areas-more">)',
        r"\1" + area_inner + r"\2",
        html,
        count=1,
    )
    if n1 != 1:
        raise SystemExit("areas-grid replace failed")

    html, n2 = re.subn(
        r'(<div id="service-areas-grid-rotated" class="service-areas-grid-min">\s*)[\s\S]*?(\s*</div>\s*<p class="view-all">)',
        r"\1" + pop_inner + r"\2",
        html,
        count=1,
    )
    if n2 != 1:
        raise SystemExit("service-areas-grid-rotated replace failed")

    INDEX.write_text(html, encoding="utf-8")
    print(
        f"index.html: areas + popular lists (Chicago DOY={seed}, "
        f"{len(area_cities)} cards, {len(pop_cities)} links)"
    )


if __name__ == "__main__":
    main()
