# MinnDrive Events — Quick Start Guide

**For operators who need to maintain the automated events pipeline.**

---

## ✅ Daily Health Check (30 seconds)

```bash
cd minndrive_website
python3 scripts/pipeline_status.py
```

**Look for:**
- Total events ~2,500+
- Next 7 days: 200+
- Next 30 days: 800+
- Missing city/URL: Low numbers
- Last scrape: Recent timestamp

---

## 🔄 Force Refresh (when data seems stale)

```bash
cd minndrive_website

# Quick refresh (weekly sources: TM, Eventbrite, Minneapolis)
python3 scripts/run_all_scrapers.py --weekly

# Full refresh (all sources including fairs/festivals)
python3 scripts/run_all_scrapers.py
```

Takes 2-5 minutes. Logs to `docs/data/scrape-run.log`.

---

## 🔍 Check What Broke

```bash
# Last 20 log lines
tail -20 docs/data/scrape-run.log

# Last scrape summary
cat docs/data/scrape-run-summary.json

# Test individual scraper
python3 scripts/fetch_tm_events.py
python3 scripts/scrape_eventbrite_emails.py
```

---

## 🧹 Fix Data Quality Issues

```bash
# Fill missing cities, normalize categories
python3 scripts/fix_data_quality.py

# Dedup (removes duplicates, cleans schema)
python3 scripts/dedup_master.py
```

---

## 📧 Gmail Auth (if Eventbrite scraper fails with auth error)

```bash
gog auth --account=minndriveairport@gmail.com
```

Follow browser OAuth flow. Tokens stored in `~/.gog/`.

---

## 🚨 Emergency: Events Page Broken

1. Check events-master.json exists: `ls -lh docs/data/events-master.json`
2. Validate JSON: `python3 -c "import json; json.load(open('docs/data/events-master.json'))"`
3. Restore backup: `cp docs/data/events-master.backup.json docs/data/events-master.json`
4. Re-run scrapers: `python3 scripts/run_all_scrapers.py`

---

## 📊 View Events Breakdown

```bash
python3 -c "
import json
d=json.load(open('docs/data/events-master.json'))
from collections import Counter
cats = Counter(e.get('category','') for e in d['events'])
for c,n in cats.most_common():
    print(f'{c:15s} {n:4d}')
"
```

---

## 🔧 Cron Jobs (should be running automatically)

```bash
crontab -l | grep minndrive
```

**Expected:**
- Weekly scrape: Sun 3 AM
- Monthly scrape: 1st of month 3 AM

**To edit:**
```bash
crontab -e
```

**Current schedule:**
```cron
# Weekly scrape (Sun 3 AM)
0 3 * * 0 cd /path/to/minndrive_website && python3 scripts/run_all_scrapers.py --weekly

# Monthly scrape (1st of month, 3 AM)
0 3 1 * * cd /path/to/minndrive_website && python3 scripts/run_all_scrapers.py --monthly
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `docs/data/events-master.json` | Primary events database (2,936 events) |
| `docs/data/events-master.backup.json` | Auto-backup before dedup |
| `docs/data/scrape-run.log` | Append-only scrape history |
| `docs/data/scrape-run-summary.json` | Last run stats |
| `scripts/run_all_scrapers.py` | **Main cron entrypoint** |
| `scripts/dedup_master.py` | **Comprehensive dedup** |

---

## 🆘 Common Issues

### "0 events in next 7 days"
→ Events DB is stale or empty  
→ Run: `python3 scripts/run_all_scrapers.py --weekly`

### "Eventbrite scraper returns 0"
→ Gmail auth expired  
→ Run: `gog auth --account=minndriveairport@gmail.com`

### "Ticketmaster scraper fails"
→ API key might be expired or rate-limited  
→ Check: `TM_API_KEY` in `scripts/fetch_tm_events.py`  
→ Wait 1 hour and retry

### "Website shows old events"
→ Browser cache  
→ Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)

### "Missing cities/URLs increased"
→ New scraper added without quality mapping  
→ Run: `python3 scripts/fix_data_quality.py`

---

## 🔗 Resources

- **Full documentation:** `EVENTS_PIPELINE.md`
- **Script reference:** `scripts/README.md`
- **GitHub repo:** `dhakgilim/openclaw` (auto-synced)
- **Live site:** GitHub Pages — `https://dhakgilim.github.io/hazeltine/`

---

## 💡 Pro Tips

1. **Before making changes:** `cp docs/data/events-master.json docs/data/events-master.backup.json`
2. **Test scrapers individually** before blaming the orchestrator
3. **Check Git status** — workspace auto-commits hourly to GitHub
4. **Monitor logs** with `tail -f docs/data/scrape-run.log` during runs
5. **Dry-run first:** `python3 scripts/run_all_scrapers.py --dry-run`

---

**Questions?** Check `EVENTS_PIPELINE.md` or ping Rick via Discord.

**Last Updated:** 2026-03-15 by Rick C-137
