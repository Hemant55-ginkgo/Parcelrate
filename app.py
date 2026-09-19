"""
ParcelRate — DE Domestic Shipping Comparator
Streamlit app · Phase 1
"""

import json
from pathlib import Path

import streamlit as st

from logic import load_rates, get_results, ineligible_reason
from location import resolve, format_option

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ParcelRate · DE Shipping Comparator",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

  /* Header */
  .pr-header {
    background: #1A2B4A;
    padding: 18px 28px;
    border-radius: 10px;
    margin-bottom: 24px;
    display: flex;
    align-items: baseline;
    gap: 10px;
  }
  .pr-logo    { font-size: 1.3rem; font-weight: 700; color: #fff; letter-spacing: -0.02em; }
  .pr-logo span { color: #60A5FA; }
  .pr-sub     { font-size: 0.75rem; color: rgba(255,255,255,0.45); }

  /* Step indicator */
  .pr-steps {
    display: flex;
    gap: 6px;
    align-items: center;
    margin-bottom: 24px;
    font-size: 0.78rem;
    font-weight: 500;
  }
  .pr-step        { color: #9CA3AF; }
  .pr-step.active { color: #1A2B4A; font-weight: 700; }
  .pr-step.done   { color: #6B7280; }
  .pr-sep         { color: #D1D5DB; }

  /* Notice */
  .pr-notice {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 0.8rem;
    color: #1E40AF;
    margin-bottom: 16px;
  }

  /* Carrier cards */
  .carrier-card {
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 10px;
    background: #fff;
  }
  .carrier-card.ineligible { opacity: 0.45; }
  .carrier-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    margin-bottom: 8px;
  }
  .badge-DHL { background: #1A2B4A; color: #FFCC00; }
  .badge-DPD { background: #DC2626; color: #fff; }
  .badge-GLS { background: #1A7C3E; color: #fff; }
  .badge-UPS { background: #5C3A1E; color: #fff; }

  .price-big {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1A2B4A;
    letter-spacing: -0.03em;
  }
  .card-meta  { font-size: 0.78rem; color: #6B7280; margin-top: 2px; }
  .card-track { font-size: 0.72rem; font-weight: 600; color: #16A34A; }
  .inelig-msg { font-size: 0.8rem; color: #DC2626; font-weight: 500; margin-top: 4px; }

  /* Tier table */
  .tier-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; margin-top: 12px; }
  .tier-table th {
    background: #F3F4F6; color: #374151;
    padding: 6px 10px; text-align: left; font-weight: 600;
    border-bottom: 1px solid #E5E7EB;
  }
  .tier-table td { padding: 7px 10px; border-bottom: 1px solid #F3F4F6; color: #1C1C1E; }
  .tier-table tr:last-child td { border-bottom: none; }
  .tier-best td { background: #F0FDF4; font-weight: 600; }

  /* Admin */
  .admin-section {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    padding: 20px;
    margin-top: 32px;
  }

  /* Route chip */
  .route-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.8rem;
    color: #1A2B4A;
    margin-bottom: 20px;
  }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
def _init():
    defaults = {
        "step": 1,
        "origin": None,   # {"postcode":..., "city":..., "state":...}
        "dest":   None,
        "origin_query": "",
        "dest_query": "",
        "weight": None,
        "dim_l": None, "dim_w": None, "dim_h": None,
        "content": "",
        "show_admin": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ── Rate card (admin-editable via session) ────────────────────────────────────
if "rates" not in st.session_state:
    st.session_state["rates"] = load_rates()


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="pr-header">
  <div class="pr-logo">Parcel<span>Rate</span></div>
  <div class="pr-sub">DE Domestic · Phase 1</div>
</div>
""", unsafe_allow_html=True)


# ── Step indicator ────────────────────────────────────────────────────────────
def step_html(current):
    steps = ["Route", "Parcel", "Compare"]
    parts = []
    for i, name in enumerate(steps, 1):
        cls = "active" if i == current else ("done" if i < current else "pr-step")
        parts.append(f'<span class="pr-step {cls}">{name}</span>')
        if i < 3:
            parts.append('<span class="pr-sep">›</span>')
    return f'<div class="pr-steps">{"".join(parts)}</div>'

st.markdown(step_html(st.session_state["step"]), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# STEP 1 — Route
# ══════════════════════════════════════════════════════
if st.session_state["step"] == 1:
    st.subheader("Where is the parcel going?")
    st.caption("Type a city name or 5-digit postcode — select from suggestions to confirm.")

    def location_field(label: str, key_prefix: str) -> dict | None:
        query = st.text_input(
            label,
            value=st.session_state.get(f"{key_prefix}_query", ""),
            placeholder="e.g. Berlin or 10115",
            key=f"input_{key_prefix}",
        )
        st.session_state[f"{key_prefix}_query"] = query

        if len(query.strip()) < 2:
            return st.session_state.get(key_prefix)

        with st.spinner("Looking up…"):
            options = resolve(query)

        if not options:
            st.warning("No results found. Try a different spelling or the exact postcode.")
            return st.session_state.get(key_prefix)

        labels = [format_option(o) for o in options]
        # If current confirmed value is still in the list, pre-select it
        current = st.session_state.get(key_prefix)
        default_ix = 0
        if current:
            try:
                default_ix = next(i for i, o in enumerate(options)
                                  if o["postcode"] == current["postcode"])
            except StopIteration:
                default_ix = 0

        chosen_label = st.selectbox(
            f"Select {label.lower()}",
            labels,
            index=default_ix,
            key=f"select_{key_prefix}",
            label_visibility="collapsed",
        )
        chosen = options[labels.index(chosen_label)]
        st.success(f"✓ {chosen['city']} · {chosen['postcode']}")
        return chosen

    origin = location_field("Origin *", "origin")
    dest   = location_field("Destination *", "dest")

    st.markdown('<div class="pr-notice">🔔 Carrier availability by region coming soon. All carriers shown.</div>',
                unsafe_allow_html=True)

    if st.button("Next →", type="primary", use_container_width=True):
        if not origin or not dest:
            st.error("Please select both origin and destination from the suggestions.")
        else:
            st.session_state["origin"] = origin
            st.session_state["dest"]   = dest
            st.session_state["step"]   = 2
            st.rerun()


# ══════════════════════════════════════════════════════
# STEP 2 — Parcel details
# ══════════════════════════════════════════════════════
elif st.session_state["step"] == 2:
    o, d = st.session_state["origin"], st.session_state["dest"]
    st.markdown(
        f'<div class="route-chip">● {o["city"]} ({o["postcode"]}) → {d["city"]} ({d["postcode"]})</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Parcel details")
    st.caption("We apply each carrier's own dimensional rules — order of L/W/H doesn't matter.")

    content = st.selectbox("Content type *", [
        "", "Documents", "Clothing & Apparel", "Electronics", "Books",
        "Cosmetics & Health", "Food & Beverages", "Toys & Games",
        "Home & Garden", "Other",
    ], index=0)

    weight = st.number_input("Weight (kg) *", min_value=0.1, max_value=40.0,
                             step=0.1, value=st.session_state["weight"] or 1.0,
                             help="Max 40 kg · GLS accepts up to 40 kg, others up to 31.5 kg")

    st.markdown("**Dimensions (cm) ***")
    col1, col2, col3 = st.columns(3)
    with col1: dim_l = st.number_input("Length", min_value=1.0, max_value=300.0,
                                        step=0.1, value=st.session_state["dim_l"] or 20.0)
    with col2: dim_w = st.number_input("Width",  min_value=1.0, max_value=300.0,
                                        step=0.1, value=st.session_state["dim_w"] or 15.0)
    with col3: dim_h = st.number_input("Height", min_value=1.0, max_value=300.0,
                                        step=0.1, value=st.session_state["dim_h"] or 10.0)
    st.caption("Order doesn't matter — dimensions are sorted per each carrier's rules.")

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← Back"):
            st.session_state["step"] = 1
            st.rerun()
    with col_next:
        if st.button("Compare prices →", type="primary", use_container_width=True):
            if not content:
                st.error("Please select a content type.")
            else:
                st.session_state.update({
                    "content": content,
                    "weight": weight,
                    "dim_l": dim_l, "dim_w": dim_w, "dim_h": dim_h,
                    "step": 3,
                })
                st.rerun()


# ══════════════════════════════════════════════════════
# STEP 3 — Results
# ══════════════════════════════════════════════════════
elif st.session_state["step"] == 3:
    o   = st.session_state["origin"]
    d   = st.session_state["dest"]
    wt  = st.session_state["weight"]
    L, W, H = st.session_state["dim_l"], st.session_state["dim_w"], st.session_state["dim_h"]
    cnt = st.session_state["content"]

    st.markdown(
        f'<div class="route-chip">● {o["city"]} ({o["postcode"]}) → '
        f'{d["city"]} ({d["postcode"]}) · {wt} kg · {L}×{W}×{H} cm · {cnt}</div>',
        unsafe_allow_html=True,
    )
    st.subheader("Price comparison")

    rates   = st.session_state["rates"]
    results = get_results(rates, wt, L, W, H)

    # Sort carriers: eligible cheapest-first, then ineligible
    def sort_key(item):
        carrier, tiers = item
        return (0 if tiers else 1, tiers[0]["price"] if tiers else 999)

    sorted_results = sorted(results.items(), key=sort_key)

    for carrier, tiers in sorted_results:
        eligible = len(tiers) > 0
        card_cls = "carrier-card" if eligible else "carrier-card ineligible"
        best = tiers[0] if tiers else None

        with st.container():
            st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)

            col_badge, col_info, col_price = st.columns([1, 3, 2])
            with col_badge:
                st.markdown(
                    f'<span class="carrier-badge badge-{carrier}">{carrier}</span>',
                    unsafe_allow_html=True,
                )
            with col_info:
                if eligible:
                    st.markdown(f"**{best['tier']}**")
                    dim_note = " · GLS girth rule" if best["dimRule"] == "SL" else ""
                    st.markdown(f'<div class="card-meta">⏱ {best["transit"]}{dim_note}</div>',
                                unsafe_allow_html=True)
                    st.markdown('<div class="card-track">✓ Tracked</div>', unsafe_allow_html=True)
                else:
                    st.markdown("**Not eligible**")
                    reason = ineligible_reason(carrier, rates, wt, L, W, H)
                    st.markdown(f'<div class="inelig-msg">{reason}</div>', unsafe_allow_html=True)
            with col_price:
                if eligible:
                    st.markdown(
                        f'<div class="price-big">€{best["price"]:.2f}</div>'
                        f'<div class="card-meta">best price</div>',
                        unsafe_allow_html=True,
                    )

            # Expandable tiers
            if eligible and len(tiers) > 1:
                with st.expander(f"▾ {len(tiers)} tiers available"):
                    rows = []
                    for i, t in enumerate(tiers):
                        dim_str = (f'{t["L"]}×{t["W"]}×{t["H"]} cm'
                                   if t["L"] else "No dim limit")
                        rule_lbl = {"LWH": "L×W×H", "SL": "GLS girth", "NONE": "Weight only"}
                        rows.append({
                            "": "★ Best" if i == 0 else "",
                            "Tier": t["tier"],
                            "Max kg": t["maxKg"],
                            "Dimensions": dim_str,
                            "Rule": rule_lbl.get(t["dimRule"], t["dimRule"]),
                            "Transit": t["transit"],
                            "Price": f'€{t["price"]:.2f}',
                        })
                    import pandas as pd
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("← Edit parcel"):
            st.session_state["step"] = 2
            st.rerun()
    with col_b:
        if st.button("New search", use_container_width=True):
            for k in ["step","origin","dest","origin_query","dest_query",
                      "weight","dim_l","dim_w","dim_h","content"]:
                st.session_state[k] = 1 if k == "step" else (None if k in ["origin","dest"] else "")
            st.rerun()


# ══════════════════════════════════════════════════════
# ADMIN — rate card editor (sidebar)
# ══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Admin · Rate Card Editor")
    st.caption("Changes apply immediately for this session. "
               "To make permanent changes, edit `data/rates.json` in the GitHub repo and redeploy.")

    import pandas as pd

    rates_df = pd.DataFrame(st.session_state["rates"])
    edited   = st.data_editor(
        rates_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "carrier":  st.column_config.SelectboxColumn("Carrier",   options=["DHL","DPD","UPS","GLS"]),
            "dimRule":  st.column_config.SelectboxColumn("Dim Rule",  options=["LWH","SL","NONE"]),
            "price":    st.column_config.NumberColumn("Price €",      format="€%.2f"),
            "maxKg":    st.column_config.NumberColumn("Max kg"),
            "tracking": st.column_config.CheckboxColumn("Tracking"),
        },
        key="admin_editor",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            st.session_state["rates"] = edited.to_dict("records")
            st.success("Saved for this session.")
    with col2:
        if st.button("↺ Reset", use_container_width=True):
            st.session_state["rates"] = load_rates()
            st.success("Reset to defaults.")

    st.divider()
    st.markdown("**Export current rates**")
    st.download_button(
        "Download rates.json",
        data=json.dumps(st.session_state["rates"], indent=2),
        file_name="rates.json",
        mime="application/json",
        use_container_width=True,
    )
    st.caption("Download and replace `data/rates.json` in your repo to make changes permanent.")
