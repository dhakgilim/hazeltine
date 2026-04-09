# Hazeltine Detailing — launch checklist

Operator-owned site for Miles (mobile auto detailing, Twin Cities). Canonical base URL in HTML is `https://dhakgilim.github.io/hazeltine/` until a custom domain is wired.

## Blocking before “real” launch

1. **Confirm phone** `(763) 352-7411` is Miles’s live business line (README flagged it as possibly inherited).
2. **Formspree (or other)** — In `contact.html`, replace `PLACEHOLDER` in the form `action` with a real form ID, or remove the form until email routing exists.
3. **Booking** — Replace EverTransit embeds/links everywhere with Miles’s actual stack (Calendly, Square, Jobber, etc.) and update privacy/terms if vendors change.
4. **Google Business Profile** — Claim/optimize; ensure NAP matches the site; link the correct Maps URL (currently a placeholder-style short link in footers — replace with the real GBP Maps link).
5. **Socials** — Add real Facebook, Yelp, Nextdoor (or drop icons). Do not leave MinnDrive URLs anywhere.

## SEO & technical

6. **Custom domain** — If using e.g. `hazeltinedetailing.com`, global find/replace base URL in `canonical`, `og:url`, JSON-LD, and sitemap if present.
7. **Google Search Console** — Verify property; submit sitemap; monitor coverage.
8. **City pages** — Spot-check generated `auto-detailing-*.html` for leftover ride/airport copy (fork residue).
9. **Structured data** — `aggregateRating` was removed from `index.html` until real reviews exist; add `Review` / accurate `AggregateRating` only when truthful.

## Content & trust

10. **Photos** — Real before/after, van/setup, Miles on site (replace any stock-only hero assumptions).
11. **Policies** — Privacy, terms, and refund pages are **drafts** with counsel-review banners; align cancellation/deposit language with actual operations, then attorney sign-off.
12. **README** — Keep placeholder checklist in sync as items above are completed.

## Nice-to-have

13. **all-cities.html** — Optional visual pass to match forest/gold theme from `index.html` (still purple-accent legacy).
14. **Analytics** — Confirm Metricool (or chosen analytics) is the intended tracker for this brand.
15. **404** — On GitHub Pages, ensure hosting serves `404.html` for missing paths (repo settings).

---

*Last updated from workspace pass (launch-prep edits to contact, policies, all-cities, index schema, 404).*
