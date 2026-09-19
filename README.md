# ParcelRate — DE Domestic Shipping Comparator

Compare DHL, DPD, UPS and GLS parcel rates for Germany domestic shipments.
Built with Streamlit · Phase 1.

## Features
- Smart location search: type a city name or postcode, get live suggestions
- Carrier-specific dimensional rules (DHL/DPD: L×W×H · GLS: girth-style · UPS: weight-only)
- Cheapest tier shown per carrier, all tiers expandable
- Admin panel (sidebar) to edit rate cards live — export as JSON to make permanent

---

## Local development

```bash
git clone https://github.com/YOUR_USERNAME/parcelrate.git
cd parcelrate
pip install -r requirements.txt
streamlit run app.py
```

---

## Deploy to Streamlit Community Cloud (free)

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select this repo → set **Main file path** to `app.py`
4. Click **Deploy** — your public URL is ready in ~60 seconds

---

## Updating rate cards (central admin workflow)

Rate card data lives in **`data/rates.json`**.

To update prices or add a carrier tier:
1. Edit `data/rates.json` directly on GitHub (or clone, edit, push)
2. Streamlit Community Cloud auto-redeploys on every push — no manual action needed
3. All users see the new rates immediately after redeploy (~30 seconds)

The admin sidebar also lets you edit rates live for a single session and download the updated JSON.

---

## Repo structure

```
parcelrate/
├── app.py              # Streamlit UI — all steps and admin panel
├── logic.py            # Carrier matching + dimensional rules (pure Python, no UI)
├── location.py         # City/postcode lookup via zippopotam.us + Nominatim
├── data/
│   └── rates.json      # ← Central source of truth for all carrier rates
├── .streamlit/
│   └── config.toml     # Theme and server config
├── requirements.txt
└── README.md
```

---

## Dimensional rules

| Carrier | Rule | Logic |
|---------|------|-------|
| DHL | L×W×H | All three sides sorted largest→smallest must each fit within tier |
| DPD | L×W×H | Same as DHL |
| GLS | Girth (S+L) | MAX(input) + MIN(input) ≤ MAX(tier) + MIN(tier) — middle dim not checked |
| UPS | Weight only | No published dimensional limit in Phase 1 rate card |

---

## Roadmap

- [ ] Phase 2: Postcode-to-zone carrier availability filtering
- [ ] Phase 2: International tab (DHL Paket International rates)
- [ ] Phase 3: Browser extension packaging
- [ ] Phase 3: Central rate card API (replace JSON file with hosted endpoint)
