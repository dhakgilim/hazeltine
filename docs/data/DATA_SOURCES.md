# Hazeltine vehicle events — data sources

_Last updated: 2026-03-13_

Total events: **1,123+** from **25+ sources**

## Collection Methods

| Method | Description | Sources | Events |
|---|---|---|---|
| **Ticketmaster API** | Discovery API v2, server-side via `fetch_tm_events.py` | 30 venues | ~732 |
| **WordPress Tribe Events API** | REST endpoint `/wp-json/tribe/events/v1/events/` | Hook & Ladder, Surly | ~95 |
| **WordPress Custom Post API** | REST endpoint `/wp-json/wp/v2/<type>` | Chanhassen (`wpbm-av-show`) | ~50 |
| **JSON-LD Scraping** | Structured data from `<script type="application/ld+json">` | Paisley Park, Varsity, Dakota Jazz, Canterbury | ~115 |
| **HTML Scraping** | Regex extraction from rendered HTML | Guthrie, wineries, casinos, MOA, Valleyfair | ~30 |
| **Article Parsing** | Custom parser for editorial festival guides | The Current | ~40 |
| **CSV Import** | Manual one-time imports from official schedules | Twins, MNUFC, Wolves | ~103 |

## Anti-Block Best Practices

- **5 rotated User-Agents** (Chrome/Safari/Firefox on Mac/Win/Linux)
- **Random jitter** (1-3s delay between requests)
- **Proper Accept headers** (HTML + JSON)
- **One request per site per day** (6 AM CDT cron)
- **No cookies, no sessions, no proxies** — clean stateless requests
- **Polite bot UA available** (`MinnDrive-EventBot/1.0 (+https://minndrive.com)`)
- **Audit log** at `docs/data/scrape-audit.json` — 90-day retention

## Ticketmaster API (30 Venues)

| Venue | TM Venue ID | Category |
|---|---|---|
| U.S. Bank Stadium | `KovZpZAF6ttA` | sports |
| Grand Casino Arena (Xcel) | `KovZpZA6AJdA` | sports |
| Target Center | `KovZpZAE7evA` | sports |
| Target Field | `KovZpZAEdatA` | sports |
| Huntington Bank Stadium | `KovZpZAalIvA` | sports |
| Allianz Field | `KovZ917AO4Q` | sports |
| CHS Field | `KovZ917AI7z` | sports |
| Williams Arena | `KovZpapzBe` | sports |
| 3M Arena at Mariucci | `KovZpa6pbe` | sports |
| Canterbury Park | `KovZpZAaJ1EA` | sports |
| The Armory | `KovZ917AQC0` | concerts |
| The Fillmore Minneapolis | `KovZpZAF7ItA` | concerts |
| First Avenue | `Za5ju3rKuqZDd_GOkk_FtFVIU2j4FaGxJU` | concerts |
| Palace Theatre | `KovZ917ACSf` | concerts |
| Paisley Park | `KovZpZA1IvIA` | arts |
| Orpheum Theatre | `KovZpakSUe` | theatre |
| State Theatre | `KovZpZAF76tA` | theatre |
| Pantages Theatre | `KovZpZAF7aJA` | theatre |
| Guthrie Theater | `KovZpZA1FdIA` | theatre |
| Ordway Center | `KovZpZA1IAdA` | theatre |
| Fitzgerald Theater | `KovZpZAF7InA` | theatre |
| Chanhassen Dinner Theatres | `Z7r9jZa7wL` | theatre |
| Minneapolis Institute of Arts | `KovZpZA7vIlA` | arts |
| Walker Art Center | `ZFr9jZ7adk` | arts |
| Mystic Lake | `KovZpaoTHe` | casinos |
| Treasure Island | `KovZpZAEktnA` | casinos |
| Mall of America | `KovZ917ASUc` | daytrips |
| MN Zoo (Weesner) | `KovZpZAdnAJA` | daytrips |
| Convention Center | `KovZpaoTwe` | festivals |
| RiverCentre | `KovZpZAal7tA` | festivals |

## Web Scrapers (20 Sources)

| Source | URL | Parser | Status |
|---|---|---|---|
| **Chanhassen** | `chanhassendt.com/wp-json/wp/v2/wpbm-av-show` | WP API (`chanhassen_api`) | ✅ 50 shows |
| **Guthrie Theater** | `guthrietheater.org/shows-and-tickets/2025-2026-season/` | Custom (`guthrie`) — fetches individual show pages for date ranges | ✅ 4 shows |
| **Hook & Ladder** | `thehookmpls.com/wp-json/tribe/events/v1/events/` | Tribe API (`tribe_api`) | ✅ 46 events |
| **Surly Brewing** | `surlybrewing.com/wp-json/tribe/events/v1/events/` | Tribe API (`tribe_api`) | ✅ 49 events |
| **Paisley Park** | `paisleypark.com/events` | Generic (JSON-LD) | ✅ 48 events |
| **Canterbury Park** | `canterburypark.com/events/` | Generic (JSON-LD) | ✅ 15 events |
| **Varsity Theater** | `varsitytheater.com/` | Generic (JSON-LD) | ✅ 25 events |
| **Dakota Jazz Club** | `dakotacooks.com/events/` | Generic (JSON-LD) | ✅ 27 events |
| **Mall of America** | `mallofamerica.com/events` | Generic | ✅ 12 events |
| **The Current Festivals** | `thecurrent.org/.../music-festivals-in-minnesota...2026` | Custom (`the_current_festivals`) | ✅ 40 festivals |
| **Cannon River Winery** | `cannonriverwinery.com/events/` | Generic | ✅ 10 events |
| **Schram Vineyards** | `schramvineyards.com/events` | Generic (JSON-LD) | ✅ 21 events |
| **Four Daughters** | `fourdaughtersvineyard.com/events/` | Generic (JSON-LD) | ✅ 3 events |
| **Valleyfair** | `valleyfair.com/events` | Generic | ✅ 2 events |
| **Grand Casino Hinckley** | `grandcasinomn.com/Entertain` | Generic | ⚠️ JS-rendered |
| **Grand Casino Mille Lacs** | `grandcasinomn.com/Entertain` | Generic | ⚠️ JS-rendered |
| **Running Aces** | `runningacescasino.com/entertainment/` | Generic | ⚠️ JS-rendered |
| **Cabooze** | `cabooze.com/events` | Generic | ⚠️ JS-rendered |
| **First Avenue** | `first-avenue.com/calendar/` | Generic | ⚠️ JS-rendered (WP Tribe API 404) |
| **MN Zoo** | `mnzoo.org/programs-events/` | Generic | ⚠️ JS-rendered |
| **Walker Art Center** | `walkerart.org/calendar` | Generic | ⚠️ JS-rendered |
| **Mia** | `artsmia.org/events` | Generic | ⚠️ 429 Rate Limited |
| **Stillwater** | `discoverstillwater.com/events-...` | Generic | ❌ 404 URL changed |
| **Padelford** | `padelfordboats.com/public-cruises/` | Generic | ⚠️ Timeout (seasonal May+) |

## CSV Imports (Manual)

| Source | Events | Method |
|---|---|---|
| Twins 2026 schedule | 80 home games | MLB CSV → JSON |
| MNUFC 2026 schedule | 16 home matches | MLS page → JSON |
| Timberwolves 2026 | 7 remaining home games | NBA API → JSON |

## Gmail Subscription (Backup)

- `minndriveairport@gmail.com` subscribed to Chanhassen Dinner Theatres emails
- Not actively used (WP API is primary), available as backup if API access is revoked

## Cron Schedule

| Job | Schedule | What it does |
|---|---|---|
| `fetch_tm_events.py` | Daily 6 AM CDT | Fetches all 30 TM venues server-side |
| `scrape_events.py` | Daily 6 AM CDT (after TM) | Scrapes all 20+ web sources |
| Git commit/push | Daily 6 AM CDT (after scrape) | Commits `events-master.json` changes |

## Files

| File | Purpose |
|---|---|
| `scripts/fetch_tm_events.py` | Ticketmaster API fetcher |
| `scripts/scrape_events.py` | Web scraper (all non-TM sources) |
| `docs/data/events-master.json` | Master events database |
| `docs/data/scrape-audit.json` | Scrape audit log (generated locally; gitignored) |
| `docs/data/DATA_SOURCES.md` | This file |
| `docs/data/city-venue-distances.json` | City–venue proximity for Events UI |

## Not on Ticketmaster (Static Destination Cards Only)

These venues don't sell through TM and don't have scrapable event pages:
- Northrop Auditorium
- Padelford Riverboats (seasonal)
- Minneapolis Queen
- Taylors Falls Scenic
- St. James Hotel (Red Wing)
- Northfield Historic District
- McNamara Alumni Center
- Steamboat Minnehaha

## Reviewed & Rejected Sources

| Source | URL | Why |
|---|---|---|
| Festival Guides & Reviews | `festivalguidesandreviews.com/minnesota-festivals/` | WordPress blog — no structured event data, just articles/reviews |
| Explore Minnesota | `exploreminnesota.com/things-to-do/festivals-events` | 403 Cloudflare — blocks all requests including API |
| Fine Line Music Cafe | `finelinemusic.com` | Connection refused |
| Icehouse MPLS | `icehousempls.com/events` | 404 Not Found |
