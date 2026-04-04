# Hazeltine CRM — operator checklist

Static UI preview (design only): [crm-mock](https://dhakgilim.github.io/hazeltine/crm-mock/)

---

## Scheduled implementation kickoff

| Field | Value |
|--------|--------|
| **Start** | **2026-04-05, 01:00** (America/Chicago · CDT) |
| **Scope** | Begin CRM application implementation (not the static mock): React/Vite/Tailwind, Firebase backend, roles (customer / detailer / admin), booking flow, ops dashboard, photo workflows per product spec. |
| **Before kickoff** | Ship any public-site / tweet links from the current static site; CRM is a separate track. |

If the start time slips, update this table so anyone picking up the repo sees the current plan.

---

## Product decisions (pick once; engineering wires config to match)

- [ ] **Payments for holds/deposits:** Stripe vs Square vs invoice-only / no card in app.
- [ ] **SMS:** Twilio (or other) vs email-only for v1.
- [ ] **Calendar:** In-app slots only vs sync to **Google Calendar** (which Google account(s); one shared ops calendar vs per detailer).
- [ ] **Booking auth:** Guest checkout vs required **Firebase Auth** for customers.

---

## Firebase (Google) — create, share securely

- [ ] **Firebase project** (dedicated Hazeltine project recommended for billing and data isolation).
- [ ] **Billing enabled** on the underlying GCP project (needed for Phone Auth at scale, heavier Functions usage, etc.).
- [ ] **Web app** registered → provide **`firebaseConfig`**: `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`.
- [ ] **Service account JSON** for server/admin SDK (Firestore admin, webhooks, cron) — **never** paste into public chat; use 1Password / GCP secret manager / CI secrets.
- [ ] **Authentication** providers enabled: e.g. email link, Google, Apple, phone — list which are in scope for v1.
- [ ] **Firestore**: confirm preferred **region** and any retention expectations.
- [ ] **Storage**: bucket for job photos; confirm max upload size and retention policy.
- [ ] **Optional — App Check** + reCAPTCHA Enterprise for abuse resistance on public booking.
- [ ] **Optional — Cloud Functions** region (e.g. `us-central1`) if using triggers (payments, notifications).

---

## Google Cloud / APIs (outside Firebase)

Enable as needed; prefer **server-side** keys for Geocoding/Places where possible.

- [ ] **Maps JavaScript API** — if booking uses map or address UI.
- [ ] **Geocoding API** — ZIP/address → coordinates; service-area validation.
- [ ] **Places API (Autocomplete)** — if address search (beyond ZIP).
- [ ] **Google Calendar API** — if ops calendar sync (OAuth client or service account + **calendar ID(s)** and sharing).
- [ ] **Optional — Google Analytics 4** — web `measurementId`.

---

## Payments (Stripe or Square — per decision above)

- [ ] **Test and live** keys (publishable + secret).
- [ ] **Webhook signing secret** and a **stable HTTPS** endpoint URL under our control.
- [ ] Processor dashboard: business profile, bank, statement descriptor (operator completes; no shared bank logins).

---

## SMS (if not email-only)

- [ ] Provider account (e.g. Twilio): **Account SID**, **Auth token** or API key, **from number** or Messaging Service SID.
- [ ] US **A2P / 10DLC** brand + campaign registration status as applicable.

---

## Email (transactional)

- [ ] Provider (Resend, SendGrid, Postmark, or SMTP).
- [ ] API key or SMTP credentials; **from** and **reply-to** addresses.
- [ ] Domain DNS: **SPF**, **DKIM** (and **DMARC** if using your domain).

---

## Domain, hosting, HTTPS

- [ ] **Domain** for the app (or confirm Firebase Hosting / existing GitHub Pages split: marketing vs app).
- [ ] **DNS access** for custom domain and **Firebase Auth authorized domains** if not using default `*.web.app` / `*.firebaseapp.com`.

---

## Legal / policy

- [ ] **Privacy policy** and **terms** URLs (Auth, payments, SMS, photos).
- [ ] **Photo / before-after consent** copy for customer uploads.

---

## Business / ops inputs (required for a real booking flow)

- [ ] **Service area rules** — ZIP allowlist, radius from a point, or county list.
- [ ] **Packages and pricing** for the booking UI.
- [ ] **Deposit rules** — amount, refundable window, no-show policy text.
- [ ] **Detailer roster** — who can be assigned; notification preferences (SMS/email/push later).

---

## Optional later

- [ ] **Apple Developer** — Sign in with Apple, push if a native app ships.
- [ ] **Error monitoring** (e.g. Sentry) — DSN via secrets.
- [ ] **Weather API** — live admin “routing context” strip (OpenWeather, etc.) if replacing mock data.

---

## Handoff

When items above are checked or explicitly deferred, note **date** and **owner** in `memory/` or your team tracker so implementation is not blocked on mystery credentials.
