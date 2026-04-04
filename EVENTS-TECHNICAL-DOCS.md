# MinnDrive Events System — Technical Documentation

**Last Updated:** 2026-03-14  
**Audience:** Programmers modifying the system WITHOUT AI assistance  
**Purpose:** Complete technical reference for the MinnDrive website events system

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Model](#data-model)
3. [Venue System](#venue-system)
4. [Event Categorization Engine](#event-categorization-engine)
5. [Filter System Architecture](#filter-system-architecture)
6. [filterAndSort() Function](#filterandsort-function)
7. [Destination Cards](#destination-cards)
8. [Deduplication Rules](#deduplication-rules)
9. [Scraper System](#scraper-system)
10. [TM Fetch Pipeline](#tm-fetch-pipeline)
11. [Display Formatting](#display-formatting)
12. [CSS Classes & HTML IDs](#css-classes--html-ids)
13. [Key Globals Reference](#key-globals-reference)
14. [How-To Guides](#how-to-guides)
15. [Known Quirks & Gotchas](#known-quirks--gotchas)

---

## 1. Architecture Overview

### Data Flow Diagram

```
┌─────────────────────┐
│  Ticketmaster API   │
└──────────┬──────────┘
           │
           │ fetch_tm_events.py (daily cron)
           │ • Fetches 30 TM venues
           │ • Applies JUNK_RE filter
           │ • Sports/concert reclassification
           │ • Replaces all TM events
           ▼
┌──────────────────────────────────────┐
│   docs/data/events-master.json       │
│   Unified event database             │
│   Sources: ticketmaster, scrape,     │
│            csv_import, api_import    │
└──────────┬───────────────────────────┘
           │
           │ HTTP fetch (no-cache headers)
           ▼
┌─────────────────────────────────────┐
│  docs/events.html (client-side JS)  │
│  • loadMasterEvents() on page load  │
│  • Assigns _venueKey & _cats        │
│  • Renders filter bars + event grid │
└─────────────────────────────────────┘
           │
           │ User interaction
           ▼
┌─────────────────────────────────────┐
│  Rendered Events Page               │
│  • Category tabs                    │
│  • Venue bar (tier 2)               │
│  • Sub-venue bar (tier 3)           │
│  • Destination cards                │
│  • Event cards with cal buttons     │
└─────────────────────────────────────┘

┌───────────────────────┐
│  scrape_events.py     │
│  (daily cron)         │
│  • Rotates via        │
│    .scrape-state.json │
│  • One source per run │
│  • Merges into master │
└──────────┬────────────┘
           │
           └──────────────────────┐
                                  ▼
                    docs/data/events-master.json
```

### Pipeline Flow

1. **Data Collection** (server-side, daily cron):
   - `fetch_tm_events.py`: Fetches all Ticketmaster venues → replaces TM events in master
   - `scrape_events.py`: Scrapes non-API venues → merges into master

2. **Client-Side Loading** (`events.html` lines ~950-1000):
   - `loadMasterEvents()` fetches `/data/events-master.json?v=YYYY-MM-DD`
   - Assigns `_venueKey` and `_cats` to each event (client-side enrichment)
   - Populates `masterEvents` array

3. **Filtering & Rendering**:
   - `filterAndSort()` applies category/venue/city filters
   - `renderEvents()` builds destination cards + event cards
   - `renderVenueBar()` builds dynamic venue filter buttons

---

## 2. Data Model

### events-master.json Structure

```json
{
  "lastUpdated": "2026-03-14T11:06:05.020594+00:00",
  "sources": ["ticketmaster", "scrape"],
  "events": [
    {
      "id": "48cd4782ac9f",
      "name": "Brunch at Bonfire & Barrel",
      "date": "2026-03-14",
      "time": "10:00:00",
      "venue_key": "schram-vineyards",
      "venue_name": "Schram Vineyards",
      "city": "Waconia",
      "category": "winery",
      "url": "https://example.com",
      "image": "https://example.com/image.jpg",
      "source": "scrape"
    }
  ]
}
```

### Event Object Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `id` | string | MD5 hash (first 12 chars) of `name\|date\|venue_key` | ✓ |
| `name` | string | Event name | ✓ |
| `date` | string | ISO date `YYYY-MM-DD` | ✓ |
| `time` | string | Local time `HH:MM:SS` (empty if TBA) | |
| `venue_key` | string | Matches VENUE_CONFIGS key or DESTINATIONS key | ✓ |
| `venue_name` | string | Human-readable venue name | ✓ |
| `city` | string | City name | ✓ |
| `category` | string | Primary category (see Categorization Engine) | ✓ |
| `url` | string | Ticket purchase link | |
| `image` | string | Event image URL | |
| `source` | string | One of: `ticketmaster`, `scrape`, `csv_import`, `api_import` | ✓ |
| `end_date` | string | Optional, for multi-day shows (Guthrie, Chanhassen) | |

### Source Types

1. **`ticketmaster`**: Fetched via TM Discovery API (fetch_tm_events.py)
2. **`scrape`**: Scraped from venue websites (scrape_events.py)
3. **`csv_import`**: Manually imported from CSV (future)
4. **`api_import`**: Imported from other APIs (future)

**Source Priority** (for dedup): `ticketmaster > scrape > api_import > csv_import`

### Client-Side Enrichment (loadMasterEvents)

**Location:** `events.html` lines ~950-1000

```javascript
masterEvents = (data.events||[]).filter(function(e){
  return e.date >= todayLocal;
}).map(function(e){
  return {
    name: e.name,
    dates:{start:{localDate:e.date, localTime:e.time||'', timeTBA:!e.time, noSpecificTime:!e.time}},
    _embedded:{venues:[{id:e.venue_key, name:e.venue_name, city:{name:e.city}}]},
    images: e.image ? [{url:e.image, ratio:'4_3', width:300, height:225}] : [],
    url: e.url||'',
    _venueKey: e.venue_key,          // ← CLIENT-SIDE ASSIGNMENT
    _cats: [e.category],             // ← WRAPPED IN ARRAY FOR getEventCats()
    _source: e.source||'',
  };
});
```

**Why?** The master JSON uses flat structure for simplicity. Client JS wraps it in the structure expected by TM API event format (for code reuse from the original TM-only version).

---

## 3. Venue System

### VENUE_CONFIGS (events.html lines ~65-95)

**Purpose:** TM venues with official Ticketmaster venue IDs. These are fetched by `fetch_tm_events.py`.

```javascript
const VENUE_CONFIGS = [
  {
    key:'usbank',
    label:'🏟️ U.S. Bank',
    tmId:'KovZpZAF6ttA',
    searchName:'U.S. Bank Stadium',
    city:'Minneapolis',
    cats:['sports','concerts']
  },
  // ... 30 total venues
];
```

| Field | Description |
|-------|-------------|
| `key` | Unique identifier (lowercase, no spaces) |
| `label` | Display label with emoji for filter buttons |
| `tmId` | Ticketmaster venue ID (used by fetch script) |
| `searchName` | Full official venue name (for junk detection) |
| `city` | City name |
| `cats` | Array of categories this venue belongs to |

### DESTINATIONS (events.html lines ~150-400)

**Purpose:** Non-TM venues (wineries, breweries, day trips, casinos) AND venue info cards.

```javascript
const DESTINATIONS = [
  {
    key:'schram-vineyards',
    name:'Schram Vineyards',
    city:'Waconia',
    cat:'wineries',
    cats:['wineries','concerts','daytrips'],  // optional multi-cat
    desc:'Award-winning wines, live music weekends, and dining at Bonfire & Barrel.',
    season:'Year-round',
    miles:35,
    url:'https://www.schramvineyards.com'
  },
  // ... 100+ destinations
];
```

| Field | Description |
|-------|-------------|
| `key` | Unique identifier (must match event `venue_key`) |
| `name` | Full venue name |
| `city` | City name |
| `cat` | Primary category (used if `cats` not present) |
| `cats` | Array of categories (overrides `cat`) |
| `desc` | Description shown in destination card |
| `season` | Operating season (e.g., "May–Oct", "Year-round") |
| `miles` | Distance from Minneapolis (used for Near/Far filters) |
| `url` | Venue website |

### VENUE_MULTI_CATS (events.html lines ~580-630)

**Purpose:** Override default venue categorization to add venues to multiple categories.

**IMPORTANT RULE:** Sports and Concerts are **mutually exclusive** (see EXCLUSIVE_CATS). Multi-cats only adds non-exclusive categories (daytrips, festivals, wineries).

```javascript
var VENUE_MULTI_CATS = {
  'schram-vineyards': ['wineries','concerts','daytrips'],
  'xcel': ['sports','concerts','festivals'],
  'canterbury': ['sports','daytrips'],
  // ...
};
```

### VENUE_ICON (events.html lines ~125-150)

**Purpose:** Map venue keys to emoji icons for display.

```javascript
var VENUE_ICON = {
  'usbank':'🏟️', 'xcel':'🏒', 'target':'🏀', 'targetfield':'⚾',
  'firstavenue':'🎵', 'fillmore':'🎸',
  'orpheum':'🎭', 'state':'🎭',
  'mysticlake':'🎰', 'treasure':'🎰',
  'schram-vineyards':'🍷', 'jcarver':'🍸', 'surly':'🍺',
  // ...
};
function venueIcon(key){ return VENUE_ICON[key] || '📍'; }
```

### VENUE_MILES (events.html line ~155)

**Purpose:** Auto-populated from DESTINATIONS. Used for Near/Far distance filters.

```javascript
var VENUE_MILES = {};
DESTINATIONS.forEach(function(d){ 
  if(d.miles !== undefined && !VENUE_MILES[d.key]) 
    VENUE_MILES[d.key] = d.miles; 
});
```

### VENUE_BY_KEY Lookup (events.html line ~97)

```javascript
const VENUE_BY_KEY = {};
VENUE_CONFIGS.forEach(function(v){VENUE_BY_KEY[v.key] = v});
```

---

## 4. Event Categorization Engine

### Categories

1. **sports** — Vikings, Twins, Wild, Gophers, etc.
2. **concerts** — Music venues, live music
3. **theatre** — Broadway, plays, musicals
4. **arts** — Museums, galleries, film
5. **festivals** — Expos, conventions, State Fair, Comic-Con
6. **daytrips** — Wineries, breweries, towns, boat tours
7. **wineries** — Wineries, breweries, distilleries (subset of daytrips)
8. **casinos** — Mystic Lake, Treasure Island, etc.

### EXCLUSIVE_CATS Rule (events.html line ~575)

```javascript
var EXCLUSIVE_CATS = {'sports':1, 'concerts':1};
```

**Sports and Concerts NEVER cross-tag.** If an event's primary category is `sports`, it will NEVER appear in `concerts`, even if the venue is tagged for both. This prevents Wild games from appearing in concerts.

### getEventCats() Logic (events.html lines ~635-655)

**Purpose:** Build the full list of categories an event belongs to, respecting exclusivity rules and venue multi-cats.

```javascript
function getEventCats(ev){
  var primary = (ev._cats && ev._cats.length) ? ev._cats[0] : 'daytrips';
  var vk = ev._venueKey || '';
  var multi = VENUE_MULTI_CATS[vk];
  if(!multi) return [primary];
  
  // Build merged list enforcing exclusivity:
  // 1. Sports ↔ Concerts never cross (if primary is one, never add the other)
  // 2. If primary is NOT sports/concerts, only add sports/concerts if primary matches
  var all = {};
  all[primary] = true;
  multi.forEach(function(c){
    if(EXCLUSIVE_CATS[c] && c !== primary) return; // never add sports/concerts unless it IS the primary
    all[c] = true;
  });
  return Object.keys(all);
}
```

### Examples

**Example 1: Wild game at Xcel**
- Event: `{name:'Wild vs. Avalanche', venue_key:'xcel', category:'sports'}`
- Primary: `sports`
- `VENUE_MULTI_CATS['xcel']` = `['sports','concerts','festivals']`
- Result: `['sports','festivals']` (concerts excluded because primary is sports)

**Example 2: Comic-Con at Xcel**
- Event: `{name:'Comic-Con', venue_key:'xcel', category:'festivals'}`
- Primary: `festivals`
- `VENUE_MULTI_CATS['xcel']` = `['sports','concerts','festivals']`
- Result: `['festivals']` (sports and concerts excluded because primary is NOT sports/concerts)

**Example 3: Concert at Schram Vineyards**
- Event: `{name:'Live Music Night', venue_key:'schram-vineyards', category:'concerts'}`
- Primary: `concerts`
- `VENUE_MULTI_CATS['schram-vineyards']` = `['wineries','concerts','daytrips']`
- Result: `['concerts','wineries','daytrips']` (no sports, so no exclusion)

### SEGMENT_MAP (fetch_tm_events.py lines ~45-51)

**Purpose:** Map Ticketmaster segment names to our categories.

```python
SEGMENT_MAP = {
    'Sports': 'sports',
    'Music': 'concerts',
    'Arts & Theatre': 'theatre',
    'Film': 'arts',
    'Miscellaneous': 'festivals',
}
```

### Sports Venue Reclassification (fetch_tm_events.py lines ~65-100)

**Problem:** Ticketmaster tags concerts at sports venues as "Sports" events.

**Solution:** At sports venues, apply a whitelist. If event name doesn't match `SPORTS_RE`, reclassify it as `concerts` (or `festivals` if it matches `FESTIVAL_RE`).

```python
SPORTS_VENUES = {'usbank', 'xcel', 'target', 'targetfield', 'huntington',
                 'allianz', 'chsfield', 'williams', 'mariucci', 'canterbury'}

SPORTS_RE = re.compile(r'''(?ix)  # Sports whitelist regex
    \bvs\.?\b                     # matchup format
    | \b(?:Vikings|Twins|Wild|Timberwolves|Lynx|Gophers|United\s+FC)\b
    | \b(?:Baseball|Basketball|Football|Hockey|Soccer|Tournament)\b
    # ... (see full pattern in script)
''')

FESTIVAL_RE = re.compile(r'''(?ix)
    \b(?:Dude\s+Perfect|Junk\s+Bonanza|Bike\s+Show|Car\s+Show|
        Comic\s+Con|Fan\s+Fest|Food\s+Fest|Beer\s+Fest)\b
''')

def get_event_cat(event, venue):
    tm_cat = SEGMENT_MAP.get(event['classifications'][0]['segment']['name'])
    
    # TM says Music → trust it
    if tm_cat == 'concerts':
        return 'concerts'
    
    # Sports venue: apply whitelist reclassification
    if venue['key'] in SPORTS_VENUES:
        if SPORTS_RE.search(event['name']):
            return 'sports'
        if FESTIVAL_RE.search(event['name']):
            return 'festivals'
        return 'concerts'  # Default for non-sports at sports venue
    
    return tm_cat or venue['cats'][0]
```

---

## 5. Filter System Architecture

### Three-Tier Filter System

**Tier 1: Category Tabs** (always visible)  
**Tier 2: Venue Bar** (shows when category selected)  
**Tier 3: Sub-Venue Bar** (shows for daytrips/wineries group selection)

### Tier 1: Category Tabs (events.html lines ~300-310)

```html
<button class="filter-btn cat-btn active" data-cat="all">All Events</button>
<button class="filter-btn cat-btn" data-cat="sports">🏟️ Sports</button>
<button class="filter-btn cat-btn" data-cat="concerts">🎵 Concerts</button>
<button class="filter-btn cat-btn" data-cat="theatre">🎭 Theatre</button>
<button class="filter-btn cat-btn" data-cat="casinos">🎰 Casinos</button>
<button class="filter-btn cat-btn" data-cat="wineries">🍷 Wineries & Brews</button>
<button class="filter-btn cat-btn" data-cat="arts">🎨 Arts & Culture</button>
<button class="filter-btn cat-btn" data-cat="daytrips">🚗 Day Trips</button>
<button class="filter-btn cat-btn" data-cat="festivals">🎉 Festivals / Events</button>
```

**State:** `currentCat` (global variable)  
**Click handler:** Sets `currentCat`, calls `renderVenueBar(cat)`, then `loadEvents('all', 0)`

### Tier 2: Venue Bar (Different Rendering Per Category)

**Location:** `renderVenueBar(cat)` function (events.html lines ~1100-1400)

#### A. Festivals Category

**Rendering:**
1. "All" button
2. "🎪 State Fairgrounds" button (if has events)
3. Pinned venue buttons: RiverCentre, Convention Center, Xcel
4. Near/Far distance filter buttons (📍 < 45 mi, 🚗 45+ mi)
5. City buttons (📍 Minneapolis, 📍 St. Paul, etc.)

**Distance Filter Logic:**
- Builds `festCityMiles` object from DESTINATIONS and VENUE_MILES
- Near/Far buttons:
  - Filter `cityItems` array by distance
  - Set `window._festDistCities` to matching cities
  - Hide/show city buttons via `matchCities` object
  - Call `loadEvents('all', 0)` to filter events

**City Button Logic:**
- Sets `currentCity = city`
- Sets `currentVenue = 'all'`
- Reloads events with city filter

**State Fair Button:**
- Sets `currentCity = '__statefair__'`
- Special sentinel recognized by filterAndSort()

**Pinned Venue Buttons:**
- Sets `currentVenue = 'rivercentre'` (or convention, xcel)
- When a pinned venue is selected, `filterAndSort()` shows ALL events at that venue (not just festivals)

#### B. Day Trips Category

**Rendering:**
1. "All" button
2. Group buttons: Towns, Fun & Games, Outdoors, Boat Tours, Wineries, Distilleries, Breweries, Casinos, Medical, Music

**Group Button Click:**
- Sets `currentVenue = '__dtgroup__'`
- Sets `currentCity = JSON.stringify(grpKeys)` (where grpKeys is object like `{'stillwater':1, 'excelsior':1}`)
- Calls `renderSubVenues(grp)` to show tier 3

#### C. Wineries & Brews Category

**Similar to Day Trips, but only 3 type groups:**
1. 🍷 Wineries
2. 🍸 Distilleries
3. 🍺 Breweries

**Same group → sub-venue pattern as Day Trips**

#### D. All Other Categories (Sports, Concerts, Theatre, Arts, Casinos)

**Rendering:**
- "All" button
- Individual venue buttons sorted by icon type, then alphabetical

**Example (Sports):**
```
All | 🏟️ U.S. Bank | 🏒 Grand Casino Arena | 🏀 Target Center | ⚾ Target Field | ...
```

**Sort Logic (events.html lines ~1390-1410):**
```javascript
venues.forEach(function(v){
  var icon = venueIcon(v.key);
  var ORDER = {'🏟️':0,'🏒':1,'🏀':2,'⚾':3,...};
  v._sortIcon = ORDER[icon] || 80;
  v._sortName = v.label.replace(/^[^\w]+ /, '').toLowerCase();
});
venues.sort(function(a,b){
  if(a._sortIcon !== b._sortIcon) return a._sortIcon - b._sortIcon;
  return a._sortName < b._sortName ? -1 : 1;
});
```

### Tier 3: Sub-Venue Bar (Day Trips / Wineries Groups)

**Location:** `renderSubVenues(grp)` function (events.html lines ~1200-1280)

**Rendering:**
1. "All [Group Name]" button
2. Near/Far distance filter buttons (📍 < 45 mi, 🚗 45+ mi)
3. Individual venue buttons: `🍷 Schram Vineyards · Waconia`

**Distance Filter Logic:**
- Builds `nearKeys` object from `VENUE_MILES` and `grp.keys`
- Near/Far buttons hide/show individual venue buttons via `.sub-venue-individual` class
- Sets `currentCity = JSON.stringify(nearKeys)`

**Individual Venue Button:**
- Sets `currentVenue = '__dtgroup__'`
- Sets `currentCity = JSON.stringify({'schram-vineyards':1})`
- Single venue selected → shows only that venue's events

### The __dtgroup__ Sentinel

**Purpose:** Signal that venue filter should use the `currentCity` JSON object as a key whitelist instead of a single venue.

**How it works:**
1. User clicks group button (e.g., "Wineries")
2. Code sets: `currentVenue = '__dtgroup__'`, `currentCity = '{"schram-vineyards":1,"alexis-bailly":1,...}'`
3. `filterAndSort()` sees `currentVenue === '__dtgroup__'` and parses `currentCity` as JSON
4. Events are filtered by: `grpKeys[e._venueKey]`

**Code (events.html lines ~795-810):**
```javascript
if(currentCity && currentCity !== 'all'){
  if(currentCity === '__statefair__'){
    filtered = filtered.filter(function(e){return e._venueKey === 'statefair'});
  } else if(venueKey === '__dtgroup__'){
    try {
      var grpKeys = JSON.parse(currentCity);
      filtered = filtered.filter(function(e){return grpKeys[e._venueKey]});
    } catch(ex){}
  } else {
    // ... city string filter
  }
}
```

### The __statefair__ Sentinel

**Purpose:** Special case for State Fair venue in festivals category.

**When set:** User clicks "🎪 State Fairgrounds" button in festivals venue bar.

**Effect:** `filterAndSort()` filters to only events where `_venueKey === 'statefair'`.

### Near/Far Distance Filters

**Cutoff:** 45 miles from Minneapolis

**For Festivals:**
- Filters **both** city buttons AND events
- Stores matched cities in `window._festDistCities` global
- City buttons get `data-city` attribute for show/hide logic

**For Day Trips / Wineries:**
- Filters **sub-venue buttons** (tier 3) via `.sub-venue-individual` class
- Stores matched venue keys in `nearKeys` object
- Sets `currentCity = JSON.stringify(nearKeys)` to filter events

**CSS Class:** `.sub-venue-individual` on individual venue buttons (required for distance hiding logic)

---

## 6. filterAndSort() Function

**Location:** events.html lines ~770-850

**Purpose:** Core filtering logic. Chains multiple filters to narrow down events.

### Filter Chain

```javascript
function filterAndSort(cat, venueKey, page){
  let filtered = masterEvents;
  
  // 1. CATEGORY FILTER
  var festivalPinnedVenues = {'statefair':1,'rivercentre':1,'convention':1,'xcel':1};
  var isPinnedFestivalVenue = (cat === 'festivals' && venueKey !== 'all' && festivalPinnedVenues[venueKey]);
  
  if(cat && cat !== 'all' && !isPinnedFestivalVenue){
    filtered = filtered.filter(function(e){
      return getEventCats(e).indexOf(cat) >= 0
    });
  }
  
  // 2. VENUE FILTER (skip if __dtgroup__)
  if(venueKey && venueKey !== 'all' && venueKey !== '__dtgroup__'){
    filtered = filtered.filter(function(e){
      return e._venueKey === venueKey
    });
  }
  
  // 3. CITY / GROUP FILTER
  if(currentCity && currentCity !== 'all'){
    // 3a. State Fair sentinel
    if(currentCity === '__statefair__'){
      filtered = filtered.filter(function(e){
        return e._venueKey === 'statefair'
      });
    }
    // 3b. __dtgroup__ key whitelist
    else if(venueKey === '__dtgroup__'){
      try {
        var grpKeys = JSON.parse(currentCity);
        filtered = filtered.filter(function(e){
          return grpKeys[e._venueKey]
        });
      } catch(ex){}
    }
    // 3c. City string filter (festivals)
    else {
      filtered = filtered.filter(function(e){
        var city = (e._embedded.venues[0].city && e._embedded.venues[0].city.name) || '';
        return city === currentCity && !festivalPinnedVenues[e._venueKey];
      });
    }
  }
  
  // 4. FESTIVAL DISTANCE FILTER
  if(window._festDistCities && cat === 'festivals' && currentCity === 'all' && venueKey === 'all'){
    filtered = filtered.filter(function(e){
      var city = (e._embedded.venues[0].city && e._embedded.venues[0].city.name) || '';
      return window._festDistCities[city] || festivalPinnedVenues[e._venueKey];
    });
  }
  
  // 5. DEDUPLICATION (by name+date)
  const seen = new Set();
  const deduped = [];
  for(const ev of filtered){
    const key = (ev.name||'').toLowerCase().replace(/\s+/g,' ').trim() + '|' + (ev.dates.start.localDate||'');
    if(!seen.has(key)){
      seen.add(key);
      deduped.push(ev);
    }
  }
  
  // 6. SORT BY DATE
  deduped.sort(function(a,b){
    return (a.dates.start.localDate||'').localeCompare(b.dates.start.localDate||'')
  });
  
  return deduped;
}
```

### Key Points

1. **Category filter skipped for pinned festival venues** — allows showing all events (concerts, sports, etc.) at RiverCentre/Convention Center/Xcel when drilled into those venues from festivals tab.

2. **Venue filter skipped when `venueKey === '__dtgroup__'`** — the group filter logic happens in step 3b instead.

3. **City filter has 3 branches:**
   - `'__statefair__'` → filter to `statefair` venue key
   - `'__dtgroup__'` mode → parse JSON, filter by key whitelist
   - Normal string → filter by city name (festivals category)

4. **Festival distance filter** only applies when:
   - `cat === 'festivals'`
   - `currentCity === 'all'` (not drilled into a city)
   - `venueKey === 'all'` (not drilled into a venue)
   - `window._festDistCities` is set (Near/Far button clicked)

5. **Dedup uses normalized name + date** — prevents "Taylor Swift" and "taylor swift" from showing twice.

6. **Sort is simple date ascending** — no time sort (events on same day show in arbitrary order within that day).

---

## 7. Destination Cards

**Purpose:** Show venue info cards above the events grid when drilled into a specific venue or group.

### renderDestinationCards() (events.html lines ~860-910)

**When to show destination cards:**

1. **__dtgroup__ mode + currentCity set** → show destinations matching group keys
2. **Single venue drill-down** → show that venue's destination card
3. **No events found (forceAll=true)** → show all destinations for current category

```javascript
function renderDestinationCards(forceAll){
  // 1. __dtgroup__ mode: show destinations matching group keys
  if(currentVenue === '__dtgroup__' && currentCity && currentCity !== 'all'){
    try {
      var grpKeys = JSON.parse(currentCity);
      var dests = DESTINATIONS.filter(function(d){ return grpKeys[d.key]; });
      if(dests.length) return dests.map(renderDestCard).join('');
    } catch(ex){}
    return '';
  }
  
  // 2. Single venue drill-down: show that venue's card
  if(currentVenue !== 'all'){
    let dests = DESTINATIONS.filter(function(d){return d.key === currentVenue});
    if(!dests.length) return '';
    return dests.map(renderDestCard).join('');
  }
  
  // 3. No events (forceAll=true): show all category destinations
  if(forceAll){
    let dests = DESTINATIONS;
    if(currentCat && currentCat !== 'all'){
      dests = dests.filter(function(d){
        if(d.cats) return d.cats.indexOf(currentCat) >= 0;
        return d.cat === currentCat;
      });
    }
    if(!dests.length) return '';
    return dests.map(renderDestCard).join('');
  }
  
  return '';
}
```

### renderDestCard() (events.html lines ~915-930)

**Structure:**
```html
<div class="event-card destination-card">
  <div class="event-date">
    <div class="month">YEAR-ROUND</div>   <!-- or season start -->
    <div class="day">🍷</div>             <!-- venue icon -->
    <div class="dow">35mi</div>           <!-- distance -->
  </div>
  <div class="event-info">
    <h4><a href="URL">Venue Name</a></h4>
    <div class="event-venue">🍷 City — Season</div>
    <div class="event-time">Description text</div>
    <div class="event-actions">
      <a href="/book-ride/" class="event-book">Book a ride →</a>
    </div>
  </div>
</div>
```

**CSS:** `.destination-card` has `border-left: 3px solid var(--accent)` to distinguish from event cards.

---

## 8. Deduplication Rules

### Three Levels of Dedup

1. **Fetch-time dedup** (fetch_tm_events.py)
2. **Scrape-time dedup** (scrape_events.py merge_events())
3. **Client-side dedup** (filterAndSort() in events.html)

### 1. Fetch-Time Dedup (fetch_tm_events.py lines ~155-165)

**After fetching all TM venues:**

```python
# Dedup TM events by ID
seen = set()
unique_tm = []
for ev in all_tm:
    if ev['id'] not in seen:
        seen.add(ev['id'])
        unique_tm.append(ev)
```

**ID generation:** `hashlib.md5(f"{name}|{local_date}|{venue_key}".encode()).hexdigest()[:12]`

### 2. Scrape-Time Dedup (scrape_events.py lines ~1285-1310)

**When merging scraped events into master:**

```python
def merge_events(master, new_events):
    today = datetime.now().strftime('%Y-%m-%d')
    existing_ids = {e['id'] for e in master['events']}
    
    # Normalize ALL dates (catch legacy junk)
    for ev in master['events']:
        ev['date'] = normalize_date(ev['date']) or ev['date']
    
    added = 0
    for ev in new_events:
        ev['date'] = normalize_date(ev['date']) or ev['date']
        if ev['date'] >= today and ev['id'] not in existing_ids:
            master['events'].append(ev)
            existing_ids.add(ev['id'])
            added += 1
    
    # Prune past events
    master['events'] = [e for e in master['events'] if e['date'] >= today]
    
    return master
```

**Source priority:** Implemented via `existing_ids` check — if a TM event and scraped event have the same ID, the one already in master (TM, since it runs first) wins.

### 3. Client-Side Dedup (events.html lines ~825-840)

**After all filtering, before rendering:**

```javascript
// Dedup by name+date
const seen = new Set();
const deduped = [];
for(const ev of filtered){
  const key = (ev.name||'').toLowerCase().replace(/\s+/g,' ').trim() + '|' + (ev.dates.start.localDate||'');
  if(!seen.has(key)){
    seen.add(key);
    deduped.push(ev);
  }
}
```

**Why needed?** Catches cases where:
- TM and scraped events have slightly different names but same date+venue
- Manual CSV imports overlap with TM
- Event name capitalization differs

### Normalization Rules

**For dedup matching:**
1. Lowercase
2. Replace multiple spaces with single space
3. Trim whitespace
4. Concatenate with date: `"taylor swift|2026-05-15"`

**Cross-source matching:** Same ID if:
- Same date
- Same venue_key
- Normalized first 20 chars of name match

### Manual Cleanup Note

The codebase previously had a manual dedup pass that removed 124 duplicates. This is now automated via the ID-based dedup in scrape_events.py merge_events().

---

## 9. Scraper System

**Script:** `scripts/scrape_events.py`  
**Cron:** Daily run  
**State File:** `scripts/.scrape-state.json`

### Rotation via .scrape-state.json

**Purpose:** Scrape 1-2 sources per cron run (not all at once) to avoid rate limiting and spread load.

**State Structure:**
```json
{
  "last_index": 5,
  "last_source": "schram-vineyards",
  "last_run": "2026-03-14T11:06:05Z"
}
```

**Rotation Logic (lines ~1330-1350):**

```python
def get_next_source():
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
    
    last_idx = state.get('last_index', -1)
    keys = sorted(SOURCES.keys())
    next_idx = (last_idx + 1) % len(keys)
    
    state['last_index'] = next_idx
    state['last_source'] = keys[next_idx]
    state['last_run'] = datetime.now(timezone.utc).isoformat()
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    return keys[next_idx]
```

### SOURCES Config (lines ~35-125)

```python
SOURCES = {
    'grand-hinckley': {
        'url': 'https://www.grandcasinomn.com/Entertain',
        'venue_key': 'grand-hinckley',
        'venue_name': 'Grand Casino Hinckley',
        'city': 'Hinckley',
        'category': 'casino',
    },
    'chanhassen': {
        'url': 'https://www.chanhassendt.com/wp-json/wp/v2/wpbm-av-show?per_page=50',
        'venue_key': 'chanhassen',
        'venue_name': 'Chanhassen Dinner Theatres',
        'city': 'Chanhassen',
        'category': 'theatre',
        'parser': 'chanhassen_api',  # Custom parser function name
    },
    # ... 25+ sources
}
```

### Parsers

**Generic Parser:** `generic_event_extract()` (lines ~950-1070)
- Looks for JSON-LD structured data first
- Falls back to regex date patterns near text that looks like event names

**Custom Parsers:**
- `parse_guthrie()` — fetches individual show pages for date ranges
- `parse_chanhassen_api()` — WordPress REST API
- `parse_tribe_api()` — WordPress Tribe Events API (Hook & Ladder, Surly)
- `parse_state_fair()` — multi-page HTML with date headers
- `parse_the_current_festivals()` — structured bold entries with "Dates:" fields

### ID Generation (line ~135)

```python
def event_id(name, date, venue_key):
    raw = f"{name.lower().strip()}|{date}|{venue_key}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]
```

**Same ID function used everywhere** — ensures dedup works across TM, scrape, and manual imports.

### Date Normalization (normalize_date function, lines ~145-250)

**Morty-proof date parser** handles every common format:
- ISO: `2026-03-13`, `2026/03/13`, `2026.03.13`
- US: `03/13/2026`, `3-13-2026`
- Verbose: `March 13, 2026`, `13 March 2026`, `Mar 13th 2026`
- ISO timestamps: `2026-03-13T19:00:00Z`
- Unix timestamps: `1741910400`, `1741910400000`
- Day-of-week prefixes: `Thu, 13 Mar 2026`
- Compact: `20260313`

**Returns:** `YYYY-MM-DD` string or `''` if unparseable.

**Why so robust?** Scraped HTML has wildly inconsistent date formats. This function prevents bad dates from breaking the system.

### merge_events() Function (lines ~1285-1310)

**Purpose:** Merge new scraped events into master DB, dedup by ID, prune past events.

```python
def merge_events(master, new_events):
    today = datetime.now().strftime('%Y-%m-%d')
    existing_ids = {e['id'] for e in master['events']}
    
    added = 0
    for ev in new_events:
        ev['date'] = normalize_date(ev['date']) or ev['date']
        if ev['date'] >= today and ev['id'] not in existing_ids:
            master['events'].append(ev)
            existing_ids.add(ev['id'])
            added += 1
    
    # Prune past events
    before = len(master['events'])
    master['events'] = [e for e in master['events'] if e['date'] >= today]
    pruned = before - len(master['events'])
    
    # Sort by date
    master['events'].sort(key=lambda e: (e['date'], e.get('time', '')))
    
    if 'scrape' not in master.get('sources', []):
        master.setdefault('sources', []).append('scrape')
    
    print(f"  + {added} new events, pruned {pruned} past events")
    return master
```

### Scrape Audit Log

**File:** `docs/data/scrape-audit.json`  
**Purpose:** Track scrape success/failure for monitoring.

**Structure:**
```json
{
  "runs": [
    {
      "timestamp": "2026-03-14T11:06:05Z",
      "source": "schram-vineyards",
      "venue": "Schram Vineyards",
      "url": "https://www.schramvineyards.com/events",
      "status": "ok",
      "events_found": 12
    },
    {
      "timestamp": "2026-03-14T11:08:15Z",
      "source": "grand-hinckley",
      "venue": "Grand Casino Hinckley",
      "url": "https://www.grandcasinomn.com/Entertain",
      "status": "error",
      "events_found": 0,
      "error": "Failed to fetch"
    }
  ]
}
```

**Status codes:**
- `ok` — events found
- `empty` — no events found (not an error)
- `error` — fetch or parse failed

**Retention:** Last 90 days of runs kept.

---

## 10. TM Fetch Pipeline

**Script:** `scripts/fetch_tm_events.py`  
**Cron:** Daily run (before scraper)  
**API Key:** `sV8uRQ7lmPs4GaU4jAc89O8nqSlBIeZY` (line ~23)

### Venue List (lines ~28-58)

30 venues with official TM IDs. Same structure as VENUE_CONFIGS in events.html.

### JUNK_RE Pattern (lines ~61-63)

**Purpose:** Filter out placeholder/upsell TM listings.

```python
JUNK_RE = r'\bsuites?\b|\bpremium\b|\bvip\b|\bparking\b|\bguest pass\b|\bvoucher\b|\bbobblehead\b|\badd-on\b|\bint fee\b|\bstm\b|\bcabana\b|\bseating\b|\bbirthday package\b|\b\d-day ticket\b|\bpre-?show\b|\bupgrade\b|\bupsell\b|\bspotlight\b|\bstargazer\b|\bsurcharge\b|\bforfeited?\b|\bforfieted\b|\btransfer fee\b|\bSBL\b'
```

**is_junk() function (lines ~68-80):**

```python
def is_junk(name, venue_name=''):
    if JUNK_PATTERN.search(name):
        return True
    # Venue-name placeholder events (e.g., "U.S. Bank Stadium Football")
    if venue_name and name.startswith(venue_name):
        generic = name[len(venue_name):].strip(' -–')
        if generic and len(generic.split()) <= 2:
            return True
    return False
```

**Example junk events:**
- "U.S. Bank Stadium Football" (too generic)
- "Target Center Premium Seating" (upsell)
- "Wild vs. Avalanche - Parking Pass" (parking)

### Sports Venue Reclassification (lines ~85-145)

**See Event Categorization Engine section** for full details.

**Key insight:** TM tags concerts at sports venues as "Sports". We apply a whitelist regex. If event doesn't match sports patterns, reclassify as `concerts` (or `festivals` if matches festival patterns).

### Fetch Logic (fetch_venue_events, lines ~150-210)

```python
def fetch_venue_events(venue, today_str):
    events = []
    page = 0
    start_dt = f"{today_str}T00:00:00Z"
    
    while True:
        url = (f"{TM_BASE}?venueId={venue['tmId']}&size=100&page={page}"
               f"&sort=date,asc&startDateTime={start_dt}&apikey={TM_API_KEY}")
        
        try:
            req = Request(url, headers={'User-Agent': 'MinnDrive-EventFetch/1.0'})
            with urlopen(req, timeout=15, context=SSL_CTX) as resp:
                data = json.loads(resp.read())
        except HTTPError as e:
            if e.code == 429:  # Rate limit
                time.sleep(2)
                continue
            break
        
        raw_events = data.get('_embedded', {}).get('events', [])
        if not raw_events:
            break
        
        for ev in raw_events:
            name = ev.get('name', '')
            local_date = ev.get('dates', {}).get('start', {}).get('localDate', '')
            
            if local_date < today_str or is_junk(name, venue['name']):
                continue
            
            cat = get_event_cat(ev, venue)
            eid = hashlib.md5(f"{name}|{local_date}|{venue['key']}".encode()).hexdigest()[:12]
            
            events.append({
                'id': eid,
                'name': name,
                'date': local_date,
                'time': ev.get('dates', {}).get('start', {}).get('localTime', ''),
                'venue_key': venue['key'],
                'venue_name': venue['name'],
                'city': venue['city'],
                'category': cat,
                'url': ev.get('url', ''),
                'image': ...,  # Best image >= 300px
                'source': 'ticketmaster',
            })
        
        page += 1
        if page >= data.get('page', {}).get('totalPages', 1):
            break
        time.sleep(0.25)  # Rate limit between pages
    
    return events
```

**Rate limiting:**
- 0.25s between pages within same venue
- 0.5s between venues (main loop, line ~240)
- 2s backoff on 429 errors

### Replace-All Strategy (lines ~220-230)

**Unlike scraper (which merges), TM fetch REPLACES all TM events:**

```python
# Remove all existing TM events
non_tm = [e for e in master['events'] if e.get('source') != 'ticketmaster']

# Prune past dates from preserved events
non_tm = [e for e in non_tm if e.get('date', '') >= today_str]

# Fetch fresh TM events
all_tm = []
for venue in VENUES:
    events = fetch_venue_events(venue, today_str)
    all_tm.extend(events)

# Merge: non-TM + fresh TM
all_events = non_tm + unique_tm
```

**Why replace instead of merge?** TM cancellations/changes wouldn't be reflected if we only added new events. Replace ensures the TM data is always current.

### Date Pruning (line ~227)

Both TM and non-TM events are pruned to remove past dates:

```python
non_tm = [e for e in non_tm if e.get('date', '') >= today_str]
```

**Prune happens daily** so the JSON doesn't grow unbounded with historical events.

### Out-of-Range Festival Filter (lines ~245-258)

**Problem:** TM API sometimes returns far-away festivals (Duluth, Fargo, Chicago).

**Solution:** Filter out festivals >120mi from Minneapolis:

```python
FAR_CITIES = {
    'Duluth', 'Brainerd', 'Milwaukee, WI', 'Chicago, IL', 'Fargo, ND', ...
}
pre_filter = len(final)
final = [e for e in final if not (
    e.get('category') == 'festivals' and e.get('city', '') in FAR_CITIES
)]
```

**Keeps:** Nearby WI border events (Eau Claire, Twin Lakes)  
**Drops:** Far ones (Milwaukee, Chicago, Fargo)

---

## 11. Display Formatting

### Time Display

**Function:** `fmtTime()` (events.html lines ~445-455)

```javascript
function fmtTime(ev){
  if(!ev.dates||!ev.dates.start) return '';
  if(ev.dates.start.timeTBA) return 'Check Times';  // ← Special handling
  if(ev.dates.start.noSpecificTime) return '';
  const t = ev.dates.start.localTime;
  if(!t) return '';
  const [h,m] = t.split(':').map(Number);
  const ampm = h>=12?'PM':'AM';
  const hr = h>12?h-12:h===0?12:h;
  return hr+':'+String(m).padStart(2,'0')+' '+ampm;
}
```

**"Check Times" instead of "Time TBA"** — more user-friendly wording.

### Date Display

**Function:** `fmtDate()` (events.html lines ~430-440)

```javascript
function fmtDate(iso){
  // IMPORTANT: Never use new Date('YYYY-MM-DD') — it parses as UTC midnight,
  // which shifts dates back one day in US timezones.
  const [y,m,day] = iso.split('-').map(Number);
  const d = new Date(y, m-1, day);  // ← Local date parsing
  const months = ['JAN','FEB','MAR',...];
  const days = ['SUN','MON','TUE',...];
  return {month:months[d.getMonth()], day:d.getDate(), dow:days[d.getDay()]};
}
```

**Critical timezone handling:** Splits date string manually instead of using `new Date('YYYY-MM-DD')`, which would parse as UTC and shift dates back by one day in CST/CDT.

### Emoji Icons

**Venue type icons:**
```javascript
🍷 wine        🍸 distillery    🍺 brewery
🎵 music       🎭 theatre       🏒 hockey
🏟️ stadium     🏀 basketball    ⚾ baseball
🎰 casino      🎡 fair          🏛️ convention
🏘️ town        🏔️ outdoors      🚢 boat tours
🎢 amusement   🏥 medical       🎨 arts
```

**Applied:**
- Venue filter buttons: `label` field in VENUE_CONFIGS
- Destination cards: `venueIcon(d.key)` function
- Event venue display: `venue.emoji` from `getVenueInfo()`

### Calendar Buttons

**Two formats:**

1. **Google Calendar** (link)
   - URL: `https://calendar.google.com/calendar/render?...`
   - Params: `action=TEMPLATE`, `text`, `dates`, `location`, `details`, `ctz=America/Chicago`
   - Adds 5 PM day-before reminder

2. **Apple/Outlook iCal** (download .ics file)
   - Generated via `downloadICS()` function
   - VALARM with `-PT[minutes]M` trigger (5 PM previous day)
   - TZ-aware: `DTSTART;TZID=America/Chicago:...`

**Reminder text:**
```
🚗 Book your MinnDrive ride to [venue]! minndrive.com/book-ride
```

### Destination Card Layout

**Special styling:**
- `border-left: 3px solid var(--accent)` (purple left border)
- `opacity: 0.92` (slightly translucent)
- Date section shows: `SEASON | ICON | DISTANCE`
- Description in italic with lower opacity

---

## 12. CSS Classes & HTML IDs

### Filter System

| Selector | Purpose | Notes |
|----------|---------|-------|
| `#venue-bar` | Tier 2 venue filter container | `display:none` when category="all" |
| `#sub-venue-bar` | Tier 3 individual venue container | Only for daytrips/wineries groups |
| `.filter-btn` | Base class for all filter buttons | Shared styling |
| `.cat-btn` | Category tab buttons (tier 1) | Larger font size |
| `.venue-btn` | Venue filter buttons (tier 2) | Smaller font, icon-based |
| `.sub-venue-btn` | Sub-venue buttons (tier 3) | Smallest font |
| `.sub-venue-individual` | Individual venue buttons in tier 3 | **Required for distance hide/show logic** |
| `.festival-city-btn` | City buttons in festivals venue bar | Needs `data-city` attribute |
| `.active` | Active filter button state | Purple background |

### Event Display

| Selector | Purpose | Notes |
|----------|---------|-------|
| `#events-grid` | Main events container | Grid layout, `aria-live="polite"` |
| `.event-card` | Individual event card | Also used for destination cards |
| `.destination-card` | Venue info card (subclass of .event-card) | Purple left border |
| `.event-date` | Date badge (left side) | Month/Day/DOW display |
| `.event-info` | Event details (right side) | Title, venue, time, actions |
| `.event-venue` | Venue name + city | Purple accent color |
| `.event-time` | Time display | Muted color |
| `.event-book` | "Book a ride" link | Purple, bold |
| `.event-actions` | Action buttons container | Calendar + booking |
| `.event-cal-row` | Calendar buttons row | Flex layout |
| `.event-cal` | Calendar button | Small, rounded, icon + text |
| `.event-img` | Event thumbnail image | 70×70px, rounded |

### Loading States

| Selector | Purpose |
|----------|---------|
| `#events-loading` | Loading spinner (shown initially) |
| `#events-empty` | Empty state message (no results) |
| `.spinner` | Animated loading spinner |
| `#load-more` | "Load More" button (pagination) |

### Layout

| Selector | Purpose |
|----------|---------|
| `.events-hero` | Top hero section |
| `.filter-bar` | Generic filter bar container |
| `.section-inner` | Max-width content wrapper (1200px) |

---

## 13. Key Globals Reference

| Variable | Type | Description | Location |
|----------|------|-------------|----------|
| `masterEvents` | Array | All events loaded from JSON (post-enrichment) | Line ~450 |
| `currentCat` | String | Selected category ('all', 'sports', 'concerts', etc.) | Line ~445 |
| `currentVenue` | String | Selected venue ('all', venue key, or '__dtgroup__') | Line ~446 |
| `currentCity` | String | Selected city ('all', city name, '__statefair__', or JSON keys) | Line ~447 |
| `currentPage` | Number | Pagination page (0-indexed) | Line ~448 |
| `displayedEvents` | Array | Events currently shown on page (for ICS download) | Line ~449 |
| `VENUE_CONFIGS` | Array | TM venues with IDs | Line ~65 |
| `DESTINATIONS` | Array | Non-TM venues + venue info | Line ~150 |
| `VENUE_BY_KEY` | Object | Lookup: key → VENUE_CONFIGS entry | Line ~97 |
| `VENUE_ICON` | Object | Lookup: key → emoji icon | Line ~125 |
| `VENUE_MILES` | Object | Lookup: key → distance in miles | Line ~155 |
| `VENUE_MULTI_CATS` | Object | Lookup: key → array of extra categories | Line ~580 |
| `EXCLUSIVE_CATS` | Object | Categories that never cross-tag | Line ~575 |
| `festivalPinnedVenues` | Object | Venues that show all events when selected in festivals | Inline in functions |
| `window._festDistCities` | Object | Cities matching Near/Far distance filter | Set by distance filter buttons |
| `PAGE_SIZE` | Constant | Events per page (30) | Line ~940 |
| `todayLocal` | String | Today's date `YYYY-MM-DD` (client timezone) | Line ~420 |

### Helper Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `fmtDate(iso)` | Format ISO date to {month, day, dow} | Object |
| `fmtTime(ev)` | Format event time to "3:00 PM" or "Check Times" | String |
| `getVenueInfo(ev)` | Extract venue name/emoji/city from event | Object |
| `getVenueAddress(ev)` | Build full address string for calendar | String |
| `venueIcon(key)` | Get emoji icon for venue key | String |
| `getEventCats(ev)` | Get all categories event belongs to (respecting exclusivity) | Array |
| `filterAndSort(cat, venueKey, page)` | Core filter logic | Array |
| `renderDestinationCards(forceAll)` | Build destination card HTML | String |
| `renderDestCard(d)` | Build single destination card | String |
| `renderCard(ev)` | Build single event card | String |
| `renderEvents(events)` | Render events + destination cards to grid | void |
| `renderVenueBar(cat)` | Build tier 2 venue filter bar | void |
| `googleCalUrl(ev, venue)` | Build Google Calendar add URL | String |
| `downloadICS(ev, venue)` | Generate and download .ics file | void |
| `escHtml(s)` | HTML entity escape | String |
| `isJunkEvent(ev)` | Client-side junk filter (placeholder events) | Boolean |

---

## 14. How-To Guides

### A. Add a New TM Venue

**Prerequisites:** Venue has a Ticketmaster venue ID.

**Steps:**

1. **Find the TM venue ID:**
   - Search on Ticketmaster.com for the venue
   - Open event at that venue
   - Look at URL: `.../venues/[VENUE_NAME]/[VENUE_ID]?...`
   - Or use TM Discovery API venue search

2. **Add to fetch_tm_events.py VENUES list** (line ~28):
   ```python
   {
     'key': 'new-venue',
     'tmId': 'KovZpZAxxxxxx',
     'name': 'New Venue Name',
     'city': 'City Name',
     'cats': ['concerts'],  # or ['sports'], ['theatre'], etc.
   },
   ```

3. **Add to events.html VENUE_CONFIGS** (line ~65):
   ```javascript
   {
     key:'new-venue',
     label:'🎵 New Venue',  // with emoji
     tmId:'KovZpZAxxxxxx',
     searchName:'New Venue Name',
     city:'City Name',
     cats:['concerts']
   },
   ```

4. **Add icon to VENUE_ICON** (line ~125):
   ```javascript
   'new-venue':'🎵',
   ```

5. **Run fetch script manually to test:**
   ```bash
   cd scripts
   python3 fetch_tm_events.py
   ```

6. **Check output:**
   - Should see "new-venue: X events"
   - Verify events appear in `docs/data/events-master.json`
   - Load events.html in browser, check that venue shows up in filter bar

### B. Add a New Scrape-Only Venue (Winery/Brewery/Casino)

**Prerequisites:** Venue has a public events page or API endpoint.

**Steps:**

1. **Add to scrape_events.py SOURCES** (line ~35):
   ```python
   'new-winery': {
       'url': 'https://newwinery.com/events',
       'venue_key': 'new-winery',
       'venue_name': 'New Winery Name',
       'city': 'City Name',
       'category': 'winery',  # or 'casino', 'daytrips', etc.
       # 'parser': 'custom_parser_func',  # if needed
   },
   ```

2. **Add to events.html DESTINATIONS** (line ~150):
   ```javascript
   {
     key:'new-winery',
     name:'New Winery Name',
     city:'City Name',
     cat:'wineries',
     cats:['wineries','daytrips'],  // if cross-category
     desc:'Award-winning wines, tastings, and events.',
     season:'Year-round',
     miles:45,
     url:'https://newwinery.com'
   },
   ```

3. **Add icon to VENUE_ICON** (line ~125):
   ```javascript
   'new-winery':'🍷',
   ```

4. **Add to DT_GROUPS if it's a day trip** (line ~1175):
   ```javascript
   {emoji:'🍷', label:'Wineries', keys:[..., 'new-winery']},
   ```

5. **Test scraper:**
   ```bash
   cd scripts
   python3 scrape_events.py --source new-winery
   ```

6. **Check output:**
   - Should see "Found X events"
   - Verify in `docs/data/events-master.json`
   - Test in browser

**Custom Parser Needed?**
If the generic parser doesn't work, add a custom parser function to scrape_events.py:

```python
def parse_new_winery(html, cfg):
    events = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Your custom extraction logic here
    # Use BeautifulSoup, regex, or DOM parsing as needed
    
    for event in extracted_events:
        events.append({
            'id': event_id(name, date, cfg['venue_key']),
            'name': name,
            'date': normalize_date(date),
            'time': time_str or '',
            'venue_key': cfg['venue_key'],
            'venue_name': cfg['venue_name'],
            'city': cfg['city'],
            'category': cfg['category'],
            'url': event_url,
            'image': image_url,
            'source': 'scrape',
        })
    
    return events
```

Then reference it in SOURCES:
```python
'new-winery': {
    ...
    'parser': 'new_winery',  # function name (without parse_ prefix)
},
```

### C. Add a New Category

**Rare — only if launching a major new content type.**

**Steps:**

1. **Add category button to events.html** (line ~305):
   ```html
   <button class="filter-btn cat-btn" data-cat="newcat">🆕 New Category</button>
   ```

2. **Update SEGMENT_MAP in fetch_tm_events.py** if TM has events for this category:
   ```python
   SEGMENT_MAP = {
       ...
       'New TM Segment Name': 'newcat',
   }
   ```

3. **Add category to DESTINATIONS** for relevant venues:
   ```javascript
   {
     key:'some-venue',
     cats:['concerts', 'newcat'],  // add to multi-cat venues
     ...
   },
   ```

4. **Update renderVenueBar()** to handle the new category (line ~1100):
   - Add case for special filter logic if needed
   - Or default to venue-based filtering

5. **Update getEventCats()** if special cross-category rules apply.

6. **Test thoroughly** — category tabs, venue filters, event display.

### D. Add a Venue to Multiple Categories

**Use VENUE_MULTI_CATS** (line ~580):

```javascript
var VENUE_MULTI_CATS = {
  'venue-key': ['category1', 'category2', 'daytrips'],
};
```

**Remember:** Sports ↔ Concerts are exclusive. Only add non-exclusive categories (daytrips, festivals, wineries).

**Example: Adding Xcel to festivals**
```javascript
'xcel': ['sports','concerts','festivals'],
```

When a Wild game is fetched (primary=sports), it shows in sports only (not concerts).  
When Comic-Con is fetched at Xcel (primary=festivals), it shows in festivals only.

### E. Debug Why Events Aren't Showing for a Filter

**Systematic debugging checklist:**

1. **Check master JSON:**
   ```bash
   cat docs/data/events-master.json | jq '.events[] | select(.venue_key == "problem-venue")'
   ```
   - Are events present?
   - Is `date >= today`?
   - Is `category` correct?

2. **Check browser console:**
   - Open events.html, F12 console
   - Look for `masterEvents` array after load
   - Check `filterAndSort(currentCat, currentVenue, 0)` output
   - Are events filtered out by category/venue/city logic?

3. **Check getEventCats():**
   ```javascript
   // In console:
   masterEvents.filter(e => e._venueKey === 'problem-venue').map(e => ({
     name: e.name,
     cats: getEventCats(e)
   }))
   ```
   - Does event have the expected categories?

4. **Check VENUE_MULTI_CATS:**
   - Is venue key in `VENUE_MULTI_CATS`?
   - Are categories spelled correctly?

5. **Check DESTINATIONS:**
   - Is venue in DESTINATIONS array?
   - Is `cat` or `cats` field correct?

6. **Check venue bar rendering:**
   - Is venue showing up in filter buttons?
   - Is button clickable?
   - Check `currentVenue` value after clicking

7. **Check __dtgroup__ mode** (if day trips or wineries):
   - Is `currentVenue === '__dtgroup__'`?
   - Is `currentCity` a valid JSON string?
   - Parse `JSON.parse(currentCity)` — does it include the venue key?

8. **Check distance filters:**
   - Is venue hidden by Near/Far button?
   - Check `VENUE_MILES[venue_key]` — is distance correct?

9. **Check dedup logic:**
   - Are duplicate events being filtered out?
   - Check event IDs in master JSON — any collisions?

10. **Check EXCLUSIVE_CATS:**
    - If event is sports primary at a concert venue, it WON'T show in concerts.
    - Verify primary category is correct.

### F. Run the Fetch/Scrape Pipeline Manually

**TM Fetch:**
```bash
cd scripts
python3 fetch_tm_events.py
```

**Scraper (all sources):**
```bash
cd scripts
python3 scrape_events.py
```

**Scraper (specific source):**
```bash
python3 scrape_events.py --source schram-vineyards
```

**Check audit log:**
```bash
cat ../docs/data/scrape-audit.json | jq '.runs[-10:]'  # Last 10 runs
```

**Force cache bust in browser:**
```
https://www.minndrive.com/events.html?v=20260315
```

---

## 15. Known Quirks & Gotchas

### 1. The __dtgroup__ Venue Filter Skip

**Location:** `filterAndSort()` line ~790

```javascript
if(venueKey && venueKey !== 'all' && venueKey !== '__dtgroup__'){
  filtered = filtered.filter(function(e){return e._venueKey === venueKey});
}
```

**Why:** When `currentVenue === '__dtgroup__'`, the venue filter is handled by the city/group filter logic instead (step 3b). If we didn't skip it here, the venue filter would fail because no event has `_venueKey === '__dtgroup__'`.

### 2. window._festDistCities Global

**Set by:** Near/Far distance filter buttons in festivals venue bar  
**Used by:** `filterAndSort()` festival distance filter (step 4)  
**Cleared by:** "All" button in venue bar

**Why global?** The distance filter needs to persist across filter bar re-renders. Easier to use a global than pass state through multiple functions.

**Gotcha:** If you add a new category with distance filters, you need to either:
- Use a different global (`window._daytripsDistKeys`), OR
- Clear `_festDistCities` when switching categories

### 3. Festival City Buttons Need data-city Attribute

**Location:** Festival venue bar city buttons (line ~1060)

```javascript
btn.setAttribute('data-city', city);
```

**Why:** The Near/Far buttons hide/show city buttons by reading this attribute:

```javascript
venueBar.querySelectorAll('.festival-city-btn').forEach(function(cb){
  var c = cb.getAttribute('data-city');
  cb.style.display = matchCities[c] ? '' : 'none';
});
```

**If you forget it:** Distance filters won't work for that city.

### 4. .sub-venue-individual Class for Distance Hiding

**Location:** Sub-venue bar individual venue buttons (line ~1270)

```javascript
btn.className = 'filter-btn venue-btn sub-venue-btn sub-venue-individual';
```

**Why:** The Near/Far buttons in tier 3 hide/show individual venue buttons by class:

```javascript
subVenueBar.querySelectorAll('.sub-venue-individual').forEach(function(vb){
  vb.style.display = nearKeys[vk] ? '' : 'none';
});
```

**If you forget it:** Distance filters won't hide that venue button.

### 5. Festival Pinned Venues Show ALL Events

**Location:** `filterAndSort()` line ~775, `renderVenueBar()` line ~1025

```javascript
var festivalPinnedVenues = {'statefair':1,'rivercentre':1,'convention':1,'xcel':1};
var isPinnedFestivalVenue = (cat === 'festivals' && venueKey !== 'all' && festivalPinnedVenues[venueKey]);

if(cat && cat !== 'all' && !isPinnedFestivalVenue){
  filtered = filtered.filter(function(e){return getEventCats(e).indexOf(cat) >= 0});
}
```

**Why:** State Fair, RiverCentre, Convention Center, and Xcel host many event types (concerts, expos, sports). When drilling into one of these venues from the festivals tab, we want to show ALL events at that venue, not just festivals.

**Effect:** Wild game at Xcel shows up when you click "Grand Casino Arena" in the festivals venue bar.

### 6. Date Parsing Timezone Gotcha

**Location:** `fmtDate()` line ~435

```javascript
// IMPORTANT: Never use new Date('YYYY-MM-DD') — it parses as UTC midnight,
// which shifts dates back one day in US timezones.
const [y,m,day] = iso.split('-').map(Number);
const d = new Date(y, m-1, day);  // ← Local date parsing
```

**Why:** `new Date('2026-03-14')` parses as `2026-03-14T00:00:00Z` (UTC), which becomes `2026-03-13 19:00:00 CST` in Minneapolis. Events would show up one day early.

**Solution:** Split the date string manually and construct date in local timezone.

### 7. Client-Side _venueKey Assignment

**Location:** `loadMasterEvents()` line ~970

```javascript
_venueKey: e.venue_key,  // ← CLIENT-SIDE ASSIGNMENT
```

**Why:** The master JSON doesn't have an `_venueKey` field at the top level (it's just `venue_key`). The client JS adds the underscore prefix to match the structure of the original TM API response format (for code reuse).

**Gotcha:** If you try to filter by `venue_key` instead of `_venueKey` in client JS, it won't work.

### 8. EXCLUSIVE_CATS Enforcement

**Location:** `getEventCats()` line ~645

```javascript
if(EXCLUSIVE_CATS[c] && c !== primary) return; // never add sports/concerts unless it IS the primary
```

**Why:** Sports and concerts are mutually exclusive. A Wild game (primary=sports) at Xcel (multi-cats=['sports','concerts','festivals']) should NEVER appear in concerts.

**Gotcha:** If you add a venue to `VENUE_MULTI_CATS` with both 'sports' and 'concerts', only the primary category will be used. The other will be excluded.

### 9. Scraper Rotation State Persistence

**Location:** `.scrape-state.json`

**Why:** Scraping 25+ sources every day would be slow and risky (rate limits, bot detection). Rotation spreads the load: 1-2 sources per day, full rotation every ~25 days.

**Gotcha:** If you add a new source, it won't be scraped until the rotation reaches it. To scrape immediately:
```bash
python3 scrape_events.py --source new-source
```

### 10. TM Fetch Replaces ALL TM Events

**Location:** `fetch_tm_events.py` line ~220

```python
non_tm = [e for e in master['events'] if e.get('source') != 'ticketmaster']
```

**Why:** TM cancellations/date changes wouldn't be reflected if we only added new events. Replace ensures TM data is always current.

**Gotcha:** If you manually add a TM event to the JSON with `source: 'ticketmaster'`, it will be deleted on the next fetch run. Use `source: 'csv_import'` for manual additions.

### 11. Empty Events Grid Still Shows Destination Cards

**Location:** `renderEvents()` line ~855

```javascript
if(!events.length){
  var cards = renderDestinationCards(true); // force=true
  if(cards){
    grid.innerHTML = cards;
  } else {
    empty.style.display = 'block';
  }
}
```

**Why:** If a venue has no upcoming events but has a destination card (e.g., seasonal winery closed for winter), we still want to show the venue info.

**Effect:** User sees "No upcoming events for this venue" message ONLY if there's also no destination card.

### 12. Junk Event Filter Runs Client-Side Too

**Location:** `isJunkEvent()` in events.html (separate from fetch_tm_events.py `is_junk()`)

**Why:** Redundant safety net in case a junk event slips through the server-side filter.

**Gotcha:** If you update the junk patterns, update BOTH places:
- `fetch_tm_events.py` `JUNK_RE` (line ~61)
- `events.html` `isJunkEvent()` (line ~720)

---

## Appendix: File Locations Quick Reference

| File | Path | Purpose |
|------|------|---------|
| Events page | `docs/events.html` | Main events UI (client-side) |
| Master DB | `docs/data/events-master.json` | Unified event database |
| TM fetch script | `scripts/fetch_tm_events.py` | Daily TM API fetch |
| Scraper script | `scripts/scrape_events.py` | Daily venue scraper |
| Scraper state | `scripts/.scrape-state.json` | Rotation tracker |
| Scrape audit | `docs/data/scrape-audit.json` | Scrape success/failure log |

---

## Appendix: Regex Patterns Reference

### Sports Whitelist (fetch_tm_events.py lines ~85-100)

```regex
(?ix)
\bvs\.?\b                     # matchup format (strongest signal)
| \b(?:Vikings|Twins|Wild|Timberwolves|Lynx|Gophers|United\s+FC)\b  # MN teams
| \b(?:Baseball|Basketball|Football|Hockey|Soccer|Volleyball)\b     # sport names
| \b(?:Tournament|Championship|Playoffs?|Finals?)\b                 # competitions
| \b(?:Horse\s+Racing|Rodeo|Bull\s+Riding)\b                       # horse/animal
```

### Festival Patterns (fetch_tm_events.py lines ~105-115)

```regex
(?ix)
\b(?:Dude\s+Perfect|Junk\s+Bonanza|Bike\s+Show|Car\s+Show|Auto\s+Show
   |Comic\s+Con|Fan\s+Fest|Food\s+(?:Fest|Festival)|Beer\s+Fest
   |Boat\s+Show|RV\s+Show|Gun\s+Show|Fashion\s+Show)\b
```

### Junk Event Patterns (fetch_tm_events.py line ~61)

```regex
\bsuites?\b|\bpremium\b|\bvip\b|\bparking\b|\bguest pass\b
|\bvoucher\b|\bbobblehead\b|\badd-on\b|\bint fee\b|\bstm\b
|\bcabana\b|\bseating\b|\bbirthday package\b|\b\d-day ticket\b
|\bpre-?show\b|\bupgrade\b|\bupsell\b|\bspotlight\b|\bstargazer\b
```

---

## Support & Contact

For questions or issues with this system, contact:

- **Developer:** OpenClaw subagent (this documentation)
- **Owner:** Greg Lasica / MinnDrive
- **Last Updated:** 2026-03-14

**This documentation is complete.** A programmer with no AI assistance should be able to understand and modify every part of the MinnDrive events system using this reference.
