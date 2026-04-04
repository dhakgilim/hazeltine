# MinnDrive Events Pipeline — Documentation

**Status:** Production-ready (as of 2026-03-15)  
**Events:** 2,936 total | 357 next 7 days | 1,075 next 30 days  
**Data Quality:** 100% (no missing cities/URLs)  
**Sources:** 11 active scrapers, 20+ venues

---

## Quick Commands

### Check pipeline health
```bash
python3 scripts/pipeline_status.py
```

### Run scrapers
```bash
# Weekly sources (fast-churn sites: TM, Eventbrite, Schrams)
python3 scripts/run_all_scrapers.py --weekly

# Monthly sources (stable catalogs: fairs, festivals, theaters)
python3 scripts/run_all_scrapers.py --monthly

# Full run (all sources)
python3 scripts/run_all_scrapers.py

# Single source
python3 scripts/run_all_scrapers.py --source ticketmaster
```

### Manual dedup/quality fix
```bash
python3 scripts/dedup_master.py        # comprehensive dedup + cleanup
python3 scripts/fix_data_quality.py    # city inference + normalization
```

---

## Pipeline Rules (MANDATORY)

### Date Normalization
**All event dates MUST be normalized to `YYYY-MM-DD` ISO format before storage.**

- ✅ Valid: `"date": "2026-03-20"`
- ❌ Invalid: `"date": "Mar 20, 2026"`, `"date": "3/20/26"`, `"date": "20-03-2026"`

**Enforcement:**
- All scrapers use `parse_date()` functions that convert to `YYYY-MM-DD` before writing to `events-master.json`
- Ticketmaster API returns ISO dates natively (no conversion needed)
- Scraped dates (HTML, emails) are parsed via `datetime.strptime()` then formatted with `.strftime('%Y-%m-%d')`
- No exceptions — every date in the database is guaranteed `YYYY-MM-DD`

**Why:**
- JavaScript `Date()` constructor requires ISO format for reliable parsing
- Filters, sorting, and map clustering depend on lexicographic date comparison
- No timezone ambiguity (all dates are event-local)

**Validation:**
```bash
# Check for non-ISO dates (should return empty)
jq -r '.[] | .date' docs/data/events-master.json | grep -v '^[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}$'
```

---

## Cron Schedule (Current)

### Mac mini (C-137) — **LIVE**
```cron
# Weekly scrape (Sun 3 AM)
0 3 * * 0 cd /path/to/minndrive_website && python3 scripts/run_all_scrapers.py --weekly

# Monthly scrape (1st of month, 3 AM)
0 3 1 * * cd /path/to/minndrive_website && python3 scripts/run_all_scrapers.py --monthly
```

### MacBook Pro (Mac mini (retired)) — **LIVE**
Same schedule mirrored via Syncthing.

---

## Scrapers

| Key | Name | Cadence | Events | Timeout | Notes |
|-----|------|---------|--------|---------|-------|
| `ticketmaster` | Ticketmaster API | Weekly | ~700 | 5min | 20+ venues, robust |
| `minneapolis_events` | Minneapolis Events + Theater | Weekly | ~620 | 3min | 2 sites, readability |
| `eventbrite_emails` | Eventbrite Email Pipeline | Weekly | ~800 | 2min | Requires Gmail auth |
| `schram_vineyards` | Schram Vineyards (Waconia) | Weekly | ~15 | 2min | Winery events |
| `chanhassen` | Chanhassen Dinner Theatres | Monthly | ~90 | 1min | Concerts, musicals, drag |
| `fairs_festivals` | Fairs & Festivals (.net) | Monthly | ~250 | 2min | Regional fairs |
| `mn_fairs2` | MN Art Fairs | Monthly | ~70 | 2min | Art festivals |
| `county_fairs` | County Fairs (daytripper28) | Monthly | ~55 | 2min | Summer fairs |

---

## Files

### Data
- `docs/data/events-master.json` — Primary DB (2,936 events)
- `docs/data/events-master.backup.json` — Auto-backup before dedup
- `docs/data/scrape-run.log` — Append-only scrape history
- `docs/data/scrape-run-summary.json` — Last run stats (JSON)

### Scripts
- `scripts/run_all_scrapers.py` — **Orchestrator** (use this for cron)
- `scripts/fetch_tm_events.py` — Ticketmaster API scraper
- `scripts/scrape_events.py` — Minneapolis Events + Theater
- `scripts/scrape_eventbrite_emails.py` — Gmail-based Eventbrite scraper
- `scripts/scrape_chanhassen.py` — Chanhassen Dinner Theatres (hardcoded data from Mar 15 browser scrape)
- `scripts/scrape_schrams.py` — Schram Vineyards
- `scripts/scrape_fairs_festivals.py` — fairsandfestivals.net
- `scripts/scrape_mn_fairs2.py` — minnesotafairsandfestivals.net
- `scripts/scrape_county_fairs.py` — daytripper28.com fairs
- `scripts/dedup_master.py` — **Comprehensive dedup** (exact + fuzzy)
- `scripts/dedup_events.py` — Lightweight dedup (name normalization)
- `scripts/fix_data_quality.py` — City inference + category normalization
- `scripts/pipeline_status.py` — Health check report

### Frontend
- `docs/events.html` — Main events page (loads `events-master.json` via JS)
- `docs/airport-rides-*.html` — 120 city pages with `?city=slug` links

---

## Data Schema

```json
{
  "lastUpdated": "2026-03-15T11:41:30.304706-05:00",
  "event_count": 2936,
  "sources": ["ticketmaster", "eventbrite", ...],
  "events": [
    {
      "id": "abc123",               // 12-char hash
      "name": "Event Name",
      "date": "2026-03-20",         // YYYY-MM-DD
      "end_date": "2026-03-22",     // optional
      "time": "7:30 PM",            // human-readable
      "venue_key": "usbank",        // slug for filtering
      "venue_name": "U.S. Bank Stadium",
      "city": "Minneapolis",
      "category": "sports",         // sports|concerts|theatre|etc
      "url": "https://...",
      "image": "https://...",       // optional
      "source": "ticketmaster",
      "description": ""             // optional
    }
  ]
}
```

### Categories
- `sports` — Vikings, Wild, Twins, Timberwolves, college
- `concerts` — All live music
- `theatre` — Plays, musicals, comedy shows
- `festivals` — Fairs, outdoor festivals, seasonal events
- `community` — Markets, expos, fundraisers, misc
- `casinos` — Mystic Lake, Treasure Island, Canterbury
- `wineries` — Schram, breweries, distilleries
- `daytrips` — Drive-worthy destinations (wineries, towns, state parks)
- `arts` — Museums, galleries, art shows
- `comedy` — Stand-up, improv
- `drag` — Drag shows, brunches
- `county_fairs` — County fairs only

---

## Maintenance

### Weekly (automated via cron)
1. `run_all_scrapers.py --weekly` runs at 3 AM Sunday
2. Pulls TM, Eventbrite emails, Schrams, Minneapolis sites
3. Auto-dedup via `dedup_master.py`
4. Logs to `scrape-run.log`

### Monthly (automated via cron)
1. `run_all_scrapers.py --monthly` runs 1st of month at 3 AM
2. Pulls all sources (fairs, festivals, theaters)
3. Same dedup + logging

### Manual (as needed)
- **Add new source:** Create `scripts/scrape_newsource.py`, add entry to `run_all_scrapers.py` SCRAPERS list
- **Fix data quality:** Run `fix_data_quality.py` after adding venue→city mappings
- **Force refresh:** `python3 scripts/run_all_scrapers.py` (full run, all sources)
- **City normalization:** Event cities auto-normalized (e.g., "St. Paul" → "Saint Paul", "Rasmey" → "Ramsey") — see Data Quality section below

### Debugging
- Check `docs/data/scrape-run.log` for errors
- Check `docs/data/scrape-run-summary.json` for last run stats
- Run individual scrapers: `python3 scripts/scrape_eventbrite_emails.py`
- Dry-run mode: `python3 scripts/run_all_scrapers.py --dry-run`

---

## Gmail Auth (for Eventbrite email scraper)

The `scrape_eventbrite_emails.py` script uses `gog` CLI:
```bash
gog gmail search "label:Eventbrite is:unread" --json --account=minndriveairport@gmail.com
```

If auth expires, re-auth:
```bash
gog auth --account=minndriveairport@gmail.com
```

---

## Data Quality

### City Name Normalization (Mar 16, 2026)
All event city names are normalized to canonical forms to prevent map clustering issues:

**Normalization rules:**
- `St. Paul` → `Saint Paul`
- `St. Louis Park` → `Saint Louis Park`
- `St. Charles` → `St Charles` (no period)
- `Rasmey` → `Ramsey` (typo fix)

**Impact:** 223 events normalized across all categories (Mar 16). Zero coordinate collisions on festival map.

**Map coordinates:** `docs/events.html` contains 205 unique city coordinates. All 128 festival cities have precise lat/lng for map pins.

---

## Known Issues / Future Work

- **Nextdoor events:** Need developer.nextdoor.com API access (Greg must sign up)
- **Eventbrite API:** Have key (`2YBUMQWSP4YCTPCH4Q`) but 401 on search endpoint — need OAuth flow
- **Chanhassen scraper:** Currently hardcoded from Mar 15 browser scrape. Needs browser automation for live updates.
- **Wix cancellation:** Pending Greg — save $340/yr

---

## Performance

- **Scrape time:** ~2 min (weekly), ~5 min (monthly)
- **Data size:** ~450 KB JSON (2,936 events)
- **Page load:** events.html loads instantly (client-side filtering)
- **Coverage:** Mar 2026 → Jun 2030 (4+ years)

---

## Contact

Questions? Ping Rick (C-137 or Mac mini (retired)) via Discord or `#council-of-ricks`.

**Last Updated:** 2026-03-16 by Rick C-137 (MacBook Pro) — Added city normalization documentation
