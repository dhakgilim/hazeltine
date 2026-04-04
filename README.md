# Hazeltine Detailing — auto detailing (site repo)

**Business focus:** Professional **auto detailing** — paint care, interior reconditioning, and protective coatings for daily drivers, weekend cars, and fleet vehicles. This README is the operator brief for what the **public site** should communicate and how it should be organized, not a catalog of inherited MinnDrive ride pages.

**Fork note:** The codebase began as a copy of the MinnDrive static-site toolchain. Launch-quality Hazeltine work means replacing ride/airport copy, URLs, booking embeds, and SEO with detailing-specific pages and calls to action.

---

## What a strong detailing site covers

Use this as a checklist when writing `content/` and core HTML. Wording below is **industry-standard framing** — adapt tiers, prices, and guarantees to Hazeltine’s actual process.

### Core service lines (typical pro shop structure)

| Line | What customers expect | Notes for copy |
|------|------------------------|----------------|
| **Maintenance wash / express** | Safe wash, dry, wheels/tires dressed, windows | Entry tier; stress *safe* two-bucket or equivalent if that’s your standard |
| **Full exterior** | Wash, decontamination (iron/clay where appropriate), trim/tire dress, sealant or wax | Bridge between wash and correction |
| **Interior** | Vacuum, steam or extract seats/carpets, plastics, glass, odor treatment options | Call out pet hair, salt season, leather care if offered |
| **Paint correction** | Single- or multi-step machine polishing to reduce swirls, oxidation, RIDs | Set expectations: “improvement” vs “show car” — [Elite Shine](https://www.shineelitedetailing.net/service-page/elite-shine-detail-package)-style tier naming is common |
| **Ceramic coating** | Multi-year paint protection after proper prep; often packaged with wash + clay + polish | Shops like [Tito’s Auto Detail](https://titosautodetail.com/our-services/ceramic-coatings/) lead with durability, maintenance, and warranty terms |
| **Add-ons** | Engine bay, headlight restoration, PPF (or referral), glass coating, fabric/leather protection | Optional line items keep main packages readable |

### Packages and pricing (how peers present it)

- **Tiered packages** (good / better / best) with explicit inclusions and rough time on site help conversions — see [Divine Auto Detail — packages](https://divineautodetail.com/packages/) and [Martin Auto Detailing — detailing packages](https://www.martinautodetailing.com/pages/detailing-packages) for layout patterns.
- **Paint correction** is often split into 1-step vs 2-step (or “enhancement” vs “full correction”) so price matches defect level.
- **Ceramic** tiers sometimes map to product line + years of rated protection; be honest about prep and maintenance (wash schedule, avoid automatic brushes, etc.).

### Trust and local SEO

- **Before/after gallery** (consistent lighting, same panel angles where possible).
- **Service area** map or city list + “mobile vs shop” if both exist.
- **Reviews** surface (Google Business Profile, embedded testimonials).
- **Booking or quote form** above the fold on service pages; many independents use Calendly, embedded Wix/Squarespace forms, or SMS-first CTAs.
- **FAQ:** ceramic vs wax, how long it takes, rain after coating, interior dry time, fleet/volume.

---

## Hazeltine-specific placeholders (fill before launch)

- **Brand legal name / DBA** — confirm spelling and registration.
- **Phone, email, booking URL** — replace any MinnDrive/EverTransit contact blocks sitewide.
- **Physical address and/or mobile radius** — drives local schema and page copy.
- **Photos and video** — shop bay, process, finished work (with customer permission).

---

## Repository / technical appendix

The tree still contains **MinnDrive-era** assets: city landing pages, events pipeline, ride-booking specs, etc. Detailing launch does not require running the events scrapers; keep or delete that stack based on whether Hazeltine needs a blog/events calendar.

### Documentation (legacy toolchain)

- **[QUICKSTART.md](QUICKSTART.md)** — Operator quick-start (health checks, troubleshooting).
- **[EVENTS_PIPELINE.md](EVENTS_PIPELINE.md)** — Events scraping (only if you keep events).
- **[MAINTENANCE_CHECKLIST.md](MAINTENANCE_CHECKLIST.md)** — Recurring tasks.
- **[scripts/README.md](scripts/README.md)** — Script index.
- **[EVENTS-TECHNICAL-DOCS.md](EVENTS-TECHNICAL-DOCS.md)** — Deep dive on events (large file).

### Stack (current inheritance)

- Static HTML under `docs/` (historically GitHub Pages–oriented).
- Scripts for sitemap generation, link audit, city/page generators — **repoint or retire** when URLs and page types are detailing-specific.

### License

Proprietary. Replace MinnDrive copyright lines in shipped pages with Hazeltine Detailing when rebranding is complete.
