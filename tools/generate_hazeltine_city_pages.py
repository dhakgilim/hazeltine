#!/usr/bin/env python3
"""
Regenerate docs/auto-detailing-*.html to match index.html (forest/navy, city-pages.css).

Extracts from each existing file: city name (title), county (footer Serving line),
city-intro, nearby-grid. Reuses Wix/CDN hero rotation URLs from default-car-event-images.json.
"""
from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CAR_JSON = DOCS / "data" / "default-car-event-images.json"
BASE = "https://dhakgilim.github.io/hazeltine"
EVERTRANSIT = (
    "https://embed.evertransit.com/schedule.html?"
    "theme=default&api_key=b68df50df04ee485999db06c3d29a936e6a6a49995d90be994f1895a439c6d152e"
)
EVERTRANSIT_ESC = EVERTRANSIT.replace("&", "&amp;")


def hash_idx(s: str, n: int) -> int:
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) & 0x7FFFFFFF
    return h % n if n else 0


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s)


def extract_city(html: str) -> str | None:
    m = re.search(r"<title>Auto Detailing\s+(.+?),\s*MN", html, re.I)
    return m.group(1).strip() if m else None


def extract_county(html: str) -> str:
    m = re.search(
        r"Serving 120\+ cities including[^,]+,\s*([^<.]+)\.",
        html,
        re.I,
    )
    if m:
        return m.group(1).strip()
    return "the Twin Cities metro"


def extract_intro_raw(html: str) -> str:
    m = re.search(r'<p class="city-intro">([\s\S]*?)</p>', html)
    if not m:
        return ""
    return strip_tags(m.group(1))


def extract_nearby(html: str) -> str:
    m = re.search(r'(<div class="nearby-grid">[\s\S]*?</div>)', html)
    return m.group(1) if m else '<div class="nearby-grid"></div>'


def clean_intro(raw: str, city: str, county: str) -> str:
    t = re.sub(r"\s+", " ", raw).strip()
    if not t or re.search(
        r"airport|MSP|chauffeur|Book Your Ride|rideshare|flat rate.*\$|ride from|pickup time",
        t,
        re.I,
    ):
        return (
            f"Hazeltine offers mobile and bay-based auto detailing in {city}, Minnesota — serving "
            f"{county} and the greater Twin Cities. Wash & seal from $149+, interior resets, paint enhancement, "
            f"and ceramic from $899+. Request a quote for your driveway or our bay."
        )
    return t


def build_json_ld(city: str, county: str, meta_desc: str, slug: str) -> str:
    doc = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "LocalBusiness",
                "@id": BASE + "/#business",
                "name": "Hazeltine Detailing",
                "description": meta_desc,
                "url": BASE + "/",
                "telephone": "+1-763-352-7411",
                "image": BASE + "/images/hazeltine-logo.svg",
                "priceRange": "$149–$2500",
                "areaServed": {
                    "@type": "City",
                    "name": city,
                    "containedInPlace": {"@type": "State", "name": "Minnesota"},
                },
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"Do you offer mobile auto detailing in {city}?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                f"Yes. Hazeltine schedules mobile and bay appointments in {city}, {county}, "
                                "and across the Twin Cities metro. Call (763) 352-7411 or request a quote on our site."
                            ),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "What do detailing packages start at?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                "Maintenance wash and sealant tiers start around $149; interior resets around $199; "
                                "paint enhancement around $449; ceramic with correction from about $899. Final price "
                                "depends on vehicle size and condition after inspection."
                            ),
                        },
                    },
                    {
                        "@type": "Question",
                        "name": "Do you need water or power at my home?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": (
                                "We can use your exterior spigot and standard outlets when available. If not, we note it "
                                "when you request a quote and can schedule at our bay instead."
                            ),
                        },
                    },
                ],
            },
            {
                "@type": "WebPage",
                "name": f"Auto Detailing {city}, MN | Hazeltine",
                "url": f"{BASE}/auto-detailing-{slug}.html",
                "isPartOf": {"@type": "WebSite", "name": "Hazeltine Detailing", "url": BASE + "/"},
            },
        ],
    }
    return json.dumps(doc, ensure_ascii=False)


def render_page(
    *,
    city: str,
    slug: str,
    county: str,
    intro: str,
    nearby: str,
    hero_url: str,
    meta_desc: str,
) -> str:
    city_e = html_module.escape(city)
    county_e = html_module.escape(county)
    intro_e = html_module.escape(intro)
    json_ld_raw = build_json_ld(city, county, meta_desc, slug)
    et = EVERTRANSIT_ESC
    hero_url_esc = html_module.escape(hero_url)

    # County display in stat — shorten if very long
    county_stat = county if len(county) <= 22 else county[:19] + "…"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/svg+xml" href="favicon.svg"><link rel="icon" type="image/png" href="favicon.png">
<title>Auto Detailing {city_e}, MN | Hazeltine Detailing</title>
<meta name="description" content="{html_module.escape(meta_desc)}">
<link rel="canonical" href="{BASE}/auto-detailing-{slug}.html">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/city-pages.css">
<script type="application/ld+json">
{json_ld_raw}
</script>
</head>
<body>
<a href="#main" class="skip-link">Skip to main content</a>
<nav role="navigation" aria-label="Main navigation">
  <a href="index.html" class="nav-brand" aria-label="Hazeltine Detailing home">
    <img src="images/hazeltine-logo.svg" width="240" height="42" alt="Hazeltine Detailing">
  </a>
  <button class="hamburger" type="button" aria-label="Toggle menu" aria-expanded="false" onclick="this.classList.toggle('active');document.querySelector('.nav-links').classList.toggle('open');this.setAttribute('aria-expanded',this.classList.contains('active'))">
    <span></span><span></span><span></span>
  </button>
  <div class="nav-links">
    <a href="index.html#packages">Packages</a>
    <a href="index.html#service-menu">Service menu</a>
    <a href="index.html#gallery">Results</a>
    <a href="index.html#areas">Service areas</a>
    <a href="index.html#mobile-faq">Mobile FAQ</a>
    <a href="events.html">Events</a>
    <a href="{et}" target="_blank" rel="noopener nofollow" class="nav-schedule-inline">Schedule</a>
    <a href="index.html" class="nav-cta">Get quote</a>
  </div>
</nav>

<main id="main">
<section class="city-page-hero">
  <div class="hero-bg" style="background-image:url('{hero_url_esc}');"></div>
  <div class="hero-content">
    <div>
      <div class="city-breadcrumb"><a href="index.html">Home</a> · <a href="index.html#areas">Service areas</a> · {city_e}</div>
      <h1>Auto detailing in<br><span class="highlight">{city_e}, Minnesota</span></h1>
      <p class="city-intro">{intro_e}</p>
      <div class="hero-cta-row">
        <a href="index.html" class="btn-hero-gold">Get your quote →</a>
        <a href="{et}" class="btn-hero-outline" target="_blank" rel="noopener nofollow">Schedule bay</a>
        <a href="tel:+17633527411" class="btn-hero-outline">Call</a>
        <a href="events.html?city={slug}" class="btn-hero-outline">Vehicle events</a>
      </div>
    </div>
    <div class="hero-card">
      <h3>At a glance — {city_e}</h3>
      <div class="quick-stats">
        <div class="stat-box"><span class="number">{html_module.escape(county_stat)}</span><span class="label">County / area</span></div>
        <div class="stat-box"><span class="number">$149+</span><span class="label">Exterior from</span></div>
        <div class="stat-box"><span class="number">120+</span><span class="label">Metro cities</span></div>
        <div class="stat-box"><span class="number">5.0★</span><span class="label">Google avg.</span></div>
      </div>
      <div class="hero-card-ctas">
        <a href="index.html" class="btn-primary">Request a detail →</a>
        <a href="{et}" class="btn-secondary" target="_blank" rel="noopener nofollow">Schedule online →</a>
      </div>
      <a href="tel:+17633527411" class="phone-link">or call (763) 352-7411</a>
    </div>
  </div>
</section>

<div class="trust-bar">
  <div class="trust-bar-inner">
    <div class="trust-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
      Licensed &amp; Insured
    </div>
    <div class="trust-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      Pro-Grade Products
    </div>
    <div class="trust-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
      Prep-Forward Process
    </div>
    <div class="trust-item">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      Clear Package Pricing
    </div>
  </div>
</div>

<section id="packages">
  <div class="section-inner">
    <div class="section-label">Packages &amp; Pricing</div>
    <h2 class="section-title">Straightforward auto detailing packages.<br>No mystery “upsell tunnel.”</h2>
    <p class="pricing-intro">Whether you’re in <strong>{city_e}</strong> or anywhere in <strong>{county_e}</strong>, you get the same clear tiers: <strong>ceramic coating</strong>, <strong>paint correction</strong>, and <strong>interior detailing</strong> with extraction — priced from real starting points after we see the vehicle. Sedans and crossovers in the Twin Cities metro use the table below; large SUVs, heavy correction, or neglected interiors are quoted on the bay.</p>
    <div class="pricing-grid">
      <div class="price-card">
        <div class="tier-name">Maintenance Wash</div>
        <div class="tier-from">$149+<small>typical sedan / crossover</small></div>
        <ul>
          <li>Hand wash, wheels &amp; barrels</li>
          <li>Iron &amp; tar safe decon (as needed)</li>
          <li>Paint-safe dry + spray sealant</li>
          <li>Glass in &amp; out</li>
        </ul>
      </div>
      <div class="price-card">
        <div class="tier-name">Interior Reset</div>
        <div class="tier-from">$199+<small>4-door / small SUV</small></div>
        <ul>
          <li>Thorough vacuum &amp; compressed air</li>
          <li>Hot water extraction on fabric</li>
          <li>Leather clean + conditioner</li>
          <li>Plastics &amp; vents detailed</li>
        </ul>
      </div>
      <div class="price-card">
        <div class="tier-name">Paint Enhancement</div>
        <div class="tier-from">$449+<small>single-stage polish</small></div>
        <ul>
          <li>Full wash + clay / chemical decon</li>
          <li>Single-stage machine polish</li>
          <li>Removes most wash swirls &amp; haze</li>
          <li>Sealant or entry ceramic option</li>
        </ul>
      </div>
      <div class="price-card">
        <div class="tier-name">Ceramic &amp; Correction</div>
        <div class="tier-from">$899+<small>multi-stage + coating</small></div>
        <ul>
          <li>Multi-stage paint correction</li>
          <li>Surface prep for coating bond</li>
          <li>Pro-grade ceramic application</li>
          <li>Cure-time &amp; care card included</li>
        </ul>
      </div>
    </div>
    <p class="pricing-footnote">Add-ons: engine bay, headlights, pet-hair remediation — priced after photos or inspection.</p>
    <div class="cta-row">
      <a href="index.html" class="btn-primary">Get your quote →</a>
      <a href="{et}" class="btn-secondary" target="_blank" rel="noopener nofollow">Schedule a bay →</a>
    </div>
  </div>
</section>

<section>
  <div class="section-inner">
    <div class="section-label">Local</div>
    <h2 class="section-title">Detailing in {city_e}</h2>
    <p class="section-subtitle">Mobile routes and bay appointments — same Hazeltine process as Minneapolis &amp; St. Paul.</p>
    <div class="info-grid">
      <div class="info-card"><h3>Coverage</h3><p>We detail in <strong>{city_e}</strong> and across <strong>{county_e}</strong>. Tell us your address or neighborhood when you request a quote.</p></div>
      <div class="info-card"><h3>Minnesota-ready</h3><p>Road salt, pollen, and cabin grime are what we plan for — decon, extraction, and protection options matched to your vehicle.</p></div>
      <div class="info-card"><h3>Clear pricing</h3><p>Starting prices are listed upfront; final scope is confirmed after photos or an on-bay inspection — no bait-and-switch.</p></div>
      <div class="info-card"><h3>Book your way</h3><p>Request a quote on the main site, schedule a bay online, or call <strong>(763) 352-7411</strong>.</p></div>
    </div>
  </div>
</section>

<section id="city-events">
  <div class="section-inner">
    <div class="city-events-header">
      <h2>Vehicle events near {city_e}</h2>
      <p>Car shows, cruises, Monster Jam, boat &amp; RV — book a detail before you roll up.</p>
    </div>
    <div data-city-events-root="" data-city-slug="{slug}" data-city-name="{city_e}" id="city-events-root"></div>
  </div>
</section>

<section class="nearby-section">
  <div class="section-inner">
    <div class="section-label">Nearby</div>
    <h2 class="section-title">Also serving nearby</h2>
    <p class="section-subtitle">Hazeltine covers 120+ cities across the Twin Cities metro.</p>
    {nearby}
    <p class="nearby-view-all"><a href="all-cities.html">View all cities →</a></p>
  </div>
</section>

<section id="book" class="cta-banner">
  <h2>Ready in {city_e}?</h2>
  <p>Request a quote for mobile or bay detailing — wash, interior, correction, or ceramic.</p>
  <div class="cta-banner-actions">
    <a href="index.html" class="btn-white">Get your quote →</a>
    <a href="{et}" class="btn-white-outline" target="_blank" rel="noopener nofollow">Schedule online →</a>
  </div>
  <p class="cta-phone-note">Or call <a href="tel:+17633527411">(763) 352-7411</a></p>
</section>

<section id="mobile-faq">
  <div class="section-inner mobile-faq-inner">
    <div class="section-label">On-site detailing</div>
    <h2 class="section-title">Mobile FAQ</h2>
    <p class="section-subtitle">Quick answers before we roll up to {city_e}.</p>
    <div class="faq-list" style="display:flex;flex-direction:column;gap:1.25rem;margin-top:1.5rem;">
      <div class="faq-simple-block"><h3>Water &amp; power?</h3><p>We can use your spigot and outlets when available; otherwise we plan for bay scheduling.</p></div>
      <div class="faq-simple-block"><h3>Weather</h3><p>Exterior work generally needs about <strong>40°F</strong> and safe conditions; we reschedule if ice or heavy rain would hurt results.</p></div>
      <div class="faq-simple-block"><h3>Space</h3><p>A driveway or wide stall where we can open all doors; tight spots may be interior-only.</p></div>
    </div>
  </div>
</section>

<section id="faq" class="section-inner" style="padding:3rem 1.5rem 4rem;max-width:42rem;margin:0 auto;">
  <div class="section-label">FAQ</div>
  <h2 class="section-title" style="font-size:1.75rem;margin-bottom:1.5rem;">Common questions</h2>
  <div class="faq-list" style="display:flex;flex-direction:column;gap:1.25rem;">
    <div class="faq-simple-block"><h3>Do you detail in {city_e}?</h3><p>Yes — mobile and bay appointments across {city_e}, {county_e}, and the metro. Start with a quote on our homepage or call (763) 352-7411.</p></div>
    <div class="faq-simple-block"><h3>Car wash vs paint correction?</h3><p>Tunnels remove loose dirt; correction uses machine polishing to reduce swirls before sealant or ceramic.</p></div>
    <div class="faq-simple-block"><h3>Ceramic cost?</h3><p>From about $899 with proper prep; final price depends on size, paint condition, and correction stages.</p></div>
  </div>
</section>

<section class="service-areas-popular-block">
  <h2>Popular service areas</h2>
  <div class="service-areas-grid-min">
    <a href="auto-detailing-bloomington.html">Bloomington</a>
    <a href="auto-detailing-minneapolis.html">Minneapolis</a>
    <a href="auto-detailing-st-paul.html">St. Paul</a>
    <a href="auto-detailing-eden-prairie.html">Eden Prairie</a>
    <a href="auto-detailing-eagan.html">Eagan</a>
    <a href="auto-detailing-woodbury.html">Woodbury</a>
  </div>
  <p class="view-all"><a href="all-cities.html">View all 120+ cities →</a></p>
</section>
</main>

<footer>
  <div class="footer-inner">
    <div class="footer-brand">
      <a href="index.html" class="nav-brand" style="margin-bottom:1rem;">
        <img src="images/hazeltine-logo-light.svg" width="200" height="35" alt="Hazeltine Detailing">
      </a>
      <p>Twin Cities auto detailing — paint correction, ceramic coatings, interior extraction. Prep-forward, clear packages, 120+ communities including {city_e}.</p>
      <div class="footer-socials">
        <a href="https://maps.app.goo.gl/XehiTJzZWRCXkyQW9" target="_blank" rel="noopener nofollow" title="Google Maps"><img src="assets/icons/google.svg" alt="Google" width="22" height="22"></a>
      </div>
    </div>
    <div class="footer-col">
      <h3>Service</h3>
      <a href="index.html">Get your quote</a>
      <a href="{et}" target="_blank" rel="noopener nofollow">Schedule online</a>
      <a href="index.html#packages">Packages</a>
      <a href="index.html#areas">Service areas</a>
      <a href="events.html">Events</a>
    </div>
    <div class="footer-col">
      <h3>Popular cities</h3>
      <a href="auto-detailing-bloomington.html">Bloomington</a>
      <a href="auto-detailing-minneapolis.html">Minneapolis</a>
      <a href="auto-detailing-st-paul.html">Saint Paul</a>
      <a href="auto-detailing-eagan.html">Eagan</a>
    </div>
    <div class="footer-col">
      <h3>Company</h3>
      <a href="contact.html">Contact</a>
      <a href="privacy-policy.html">Privacy</a>
      <a href="terms-and-conditions.html">Terms</a>
      <a href="refund-policy.html">Refunds</a>
    </div>
  </div>
  <div class="footer-bottom">
    <span>© 2026 Hazeltine Detailing · Auto detailing {city_e}, MN</span>
  </div>
</footer>

<script src="js/city-page-events.js" defer></script>
<script>function loadScript(a){{var b=document.getElementsByTagName("head")[0],c=document.createElement("script");c.type="text/javascript",c.src="https://tracker.metricool.com/resources/be.js",c.onreadystatechange=a,c.onload=a,b.appendChild(c)}}loadScript(function(){{if(typeof beTracker!=='undefined')beTracker.t({{hash:"5c6a5ef4e3c7cca1567e6995a471fa07"}})}})</script>
</body>
</html>
"""


def main() -> None:
    urls = json.loads(CAR_JSON.read_text(encoding="utf-8")).get("urls") or []
    if not urls:
        raise SystemExit("No urls in default-car-event-images.json")

    paths = sorted(DOCS.glob("auto-detailing-*.html"))
    if not paths:
        raise SystemExit("No auto-detailing-*.html files in docs/")

    for path in paths:
        slug = path.stem.replace("auto-detailing-", "")
        html_old = path.read_text(encoding="utf-8")
        city = extract_city(html_old)
        if not city:
            # Filename fallback
            city = slug.replace("-", " ").title()
            if slug == "st-paul":
                city = "St. Paul"
            elif slug == "st-louis-park":
                city = "St. Louis Park"
            # ... many edge cases; title-case slug is OK for most
        county = extract_county(html_old)
        intro = clean_intro(extract_intro_raw(html_old), city, county)
        nearby = extract_nearby(html_old)
        hero_url = urls[hash_idx(slug, len(urls))]
        meta_desc = (
            f"Mobile auto detailing in {city}, MN — ceramic coating, paint correction, interior cleaning. "
            f"Serving {county}. Hazeltine. (763) 352-7411."
        )
        out = render_page(
            city=city,
            slug=slug,
            county=county,
            intro=intro,
            nearby=nearby,
            hero_url=hero_url,
            meta_desc=meta_desc,
        )
        path.write_text(out, encoding="utf-8")
        print(path.name)

    print(f"Done: {len(paths)} city pages.")


if __name__ == "__main__":
    main()
