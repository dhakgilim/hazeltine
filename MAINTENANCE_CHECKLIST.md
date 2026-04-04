# MinnDrive Events — Weekly Maintenance Checklist

**15-minute routine to keep the pipeline healthy.**

---

## ☑️ Week of: _________

### Monday Morning (5 min)

- [ ] **Check pipeline status**
  ```bash
  cd ~/path/to/minndrive_website
  python3 scripts/pipeline_status.py
  ```
  - [ ] Total events > 2,500
  - [ ] Next 7 days > 200 events
  - [ ] Next 30 days > 800 events
  - [ ] Last updated < 48 hours ago

- [ ] **Review last scrape**
  ```bash
  tail -30 docs/data/scrape-run.log
  ```
  - [ ] No FAIL/TIMEOUT/ERROR messages
  - [ ] All sources returned events

### If Issues Found

- [ ] **Stale data** (> 48h old)
  ```bash
  python3 scripts/run_all_scrapers.py --weekly
  ```

- [ ] **Low event count** (< 2,500)
  ```bash
  # Check which sources failed
  cat docs/data/scrape-run-summary.json
  # Re-run failed scraper
  python3 scripts/scrape_SOURCENAME.py
  ```

- [ ] **Gmail auth expired** (Eventbrite scraper fails)
  ```bash
  gog auth --account=minndriveairport@gmail.com
  ```

---

## ☑️ Monthly Tasks (first Monday of month)

- [ ] **Full scrape run** (all sources including fairs/festivals)
  ```bash
  python3 scripts/run_all_scrapers.py --monthly
  ```

- [ ] **Data quality check**
  ```bash
  python3 scripts/monitor_pipeline.py
  ```
  - [ ] Missing cities < 200
  - [ ] Missing URLs < 800

- [ ] **Run quality fix if needed**
  ```bash
  python3 scripts/fix_data_quality.py
  python3 scripts/dedup_master.py
  ```

- [ ] **Backup events DB**
  ```bash
  cp docs/data/events-master.json ~/backups/events-$(date +%Y-%m-%d).json
  ```

---

## ☑️ Quarterly Tasks (every 3 months)

- [ ] **Review venue mappings**
  - Check `scripts/fix_data_quality.py` VENUE_CITY dict
  - Add any new recurring venues

- [ ] **Update documentation**
  - Review `EVENTS_PIPELINE.md`
  - Update scraper counts/performance notes
  - Check GitHub repo sync

- [ ] **Audit scraper reliability**
  - Review `docs/data/scrape-run.log` for patterns
  - Identify consistently-failing sources
  - Consider deprecating or fixing

- [ ] **Check cron jobs**
  ```bash
  crontab -l | grep minndrive
  ```
  - Weekly: Sun 3 AM
  - Monthly: 1st 3 AM

---

## 🚨 Emergency Response

### Website shows no events
1. [ ] Check JSON file exists: `ls -lh docs/data/events-master.json`
2. [ ] Validate JSON: `python3 -c "import json; json.load(open('docs/data/events-master.json'))"`
3. [ ] Restore backup: `cp docs/data/events-master.backup.json docs/data/events-master.json`
4. [ ] Force refresh: `python3 scripts/run_all_scrapers.py`

### Scraper consistently failing
1. [ ] Test individually: `python3 scripts/scrape_SOURCENAME.py`
2. [ ] Check auth (Gmail scrapers): `gog auth --account=minndriveairport@gmail.com`
3. [ ] Check API keys (Ticketmaster): Review `TM_API_KEY` in script
4. [ ] If Cloudflare block: Note in TASK_QUEUE.md for manual browser scrape

### Events way out of date
1. [ ] Check cron is running: `crontab -l`
2. [ ] Review last 50 log lines: `tail -50 docs/data/scrape-run.log`
3. [ ] Force full refresh: `python3 scripts/run_all_scrapers.py`
4. [ ] If still stale: Contact Rick via Discord

---

## 📊 Health Metrics (normal ranges)

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Total events | 2,500+ | 2,000-2,500 | < 2,000 |
| Next 7 days | 200+ | 100-200 | < 100 |
| Next 30 days | 800+ | 500-800 | < 500 |
| Data age | < 24h | 24-48h | > 48h |
| Missing cities | < 100 | 100-200 | > 200 |
| Missing URLs | < 500 | 500-800 | > 800 |
| Failed scrapers | 0 | 1-2 | 3+ |

---

## 📝 Notes Section

**Issues encountered:**


**Fixes applied:**


**Follow-up needed:**


---

**Template Version:** 1.0 (2026-03-15)  
**Next review:** _________
