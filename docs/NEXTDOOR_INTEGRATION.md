# Nextdoor Integration Plan — MinnDrive Events

## Status: BLOCKED — Requires Greg's Manual Auth Steps

## Goal
Extract local community events from Nextdoor for the MinnDrive events page.
Focus on Chanhassen/Waconia/Chaska/Eden Prairie area events.

## Approaches Evaluated

### 1. Nextdoor Developer API (Recommended)
- **Search API**: Query events by lat/long + radius + category "events"
- **Events API**: Dedicated events endpoint (marked "coming soon" as of 2026)
- **Trending Posts API**: Top 100 posts per city, can filter for events
- **Requires**: Developer portal signup at developer.nextdoor.com
- **Pros**: Clean structured JSON, official, rate-limited but reliable
- **Cons**: Requires approval process, may take days

### 2. Gmail Pipeline (Fallback — Already Planned)
- Nextdoor sends digest emails with local events + posts
- minndriveairport@gmail.com → Gmail API → parse event data from email HTML
- **Requires**: Gmail OAuth (browser flow by Greg), Gmail labels set up
- **Pros**: No Nextdoor API needed, captures what's relevant to Greg's neighborhood
- **Cons**: Only captures events Nextdoor decides to email, delay vs real-time

### 3. Third-Party Scrapers (Expensive)
- Apify NextdoorScraper: Playwright-based, extracts posts/events to JSON
- ScrapingBee: $49-599/mo for API credits
- **Not recommended** for MinnDrive's scale — overkill and expensive

## Implementation Plan

### Phase 1: Greg Manual Steps (BLOCKING)
- [ ] Sign up at developer.nextdoor.com for API access
- [ ] OR: Complete Gmail OAuth flow for minndriveairport@gmail.com (on C-137)
- [ ] Create Gmail label: MinnDrive/Nextdoor
- [ ] Set Gmail filter: from:nextdoor → label:MinnDrive/Nextdoor

### Phase 2: Build Pipeline (After Auth)
- [ ] If API: Create `scrape_nextdoor.py` — query Search API for events near 44.8622,-93.5308 (Chanhassen)
- [ ] If Gmail: Create `parse_nextdoor_emails.py` — extract events from Nextdoor digest emails
- [ ] Dedup against events-master.json
- [ ] Add to daily scrape cron

### Phase 3: Lead Gen (Stretch)
- [ ] Keyword scan for ride-related posts ("need a ride", "airport", "shuttle", "transportation")
- [ ] Twilio SMS alert to Greg when matches found
- [ ] Track leads in a separate leads.json

## Location Config
```
center_lat: 44.8622
center_lng: -93.5308
radius_miles: 15
neighborhoods: [Chanhassen, Waconia, Chaska, Eden Prairie, Victoria, Prior Lake, Shakopee]
```

## Decision
Marking as BLOCKED in TASK_QUEUE.md. Cannot proceed without Greg completing auth steps.
Next heartbeat should pick the next available task.
