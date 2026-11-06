"""Streamlit viewer for the Mombasa e-tuktuk financing pilot (concept stage)."""
import altair as alt
import pandas as pd
import streamlit as st

from etuktuk import model as m
from etuktuk.defaults import Inputs, REGISTER, PLACEHOLDER

st.set_page_config(page_title="Mombasa e-tuktuk pilot: concept model", layout="wide")
D = Inputs()


def kes(x):
    return f"KES {x:,.0f}"


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


# ------------------------------------------------------------------ sidebar inputs
sb = st.sidebar
sb.header("Inputs")
sb.caption("Yellow-flagged (placeholder) inputs are not sourced from any lender, supplier or operator.")
if sb.button("Reset to defaults"):
    st.session_state.clear()
    st.rerun()

with sb.expander("Pilot terms", expanded=True):
    vehicles = st.number_input("Pilot fleet (vehicles)", 1, 500, D.vehicles, key="vehicles")
    scale_vehicles = st.number_input("Scale-up fleet (vehicles)", 1, 2000, D.scale_vehicles, key="scale")
    loan = st.number_input("Loan per vehicle (KES)", 100_000, 1_000_000, int(D.loan), step=10_000, key="loan")
    rate = st.number_input("Operator loan rate, % p.a.", 0.0, 40.0, D.rate * 100, step=0.5, key="rate") / 100
    term = st.selectbox("Loan term (months)", [24, 36, 48], index=1, key="term")

with sb.expander("Funding (lender's cost of funds)", expanded=True):
    scenario = st.radio("Funding scenario", ["A", "B", "C"], horizontal=True, key="scenario",
                        format_func=lambda s: {"A": "A: concessional target", "B": "B: commercial KES", "C": "C: USD funding"}[s])
    f_target = st.number_input("A: concessional target rate, %", 0.0, 30.0, D.funding_target * 100, step=0.5, key="ft") / 100
    f_com = st.number_input("B: commercial KES rate, % (placeholder)", 0.0, 40.0, D.funding_commercial * 100, step=0.5, key="fc") / 100
    f_usd = st.number_input("C: USD funding rate, % (placeholder)", 0.0, 30.0, D.funding_usd * 100, step=0.5, key="fu") / 100
    depr = st.number_input("C: KES depreciation p.a., % (placeholder)", 0.0, 30.0, D.depreciation * 100, step=0.5, key="dp") / 100

with sb.expander("Credit and cost"):
    default_rate = st.slider("Annual default rate, % (placeholder)", 0.0, 30.0, D.default_rate * 100, 0.5, key="dr") / 100
    lgd = st.slider("Loss given default, % (placeholder)", 0.0, 100.0, D.lgd * 100, 5.0, key="lgd") / 100
    admin = st.number_input("Admin cost, % of balance p.a.", 0.0, 10.0, D.admin * 100, step=0.25, key="ad") / 100

with sb.expander("Operator economics"):
    fares = st.number_input("Daily fares (KES)", 500, 5_000, int(D.fares), step=50, key="fares")
    petrol_cost = st.number_input("Petrol per day, petrol tuktuk (KES)", 100, 3_000, int(D.petrol_cost), step=50, key="pc")
    ice_maint = st.number_input("Maintenance per day, petrol (KES)", 0, 1_000, int(D.ice_maint), step=10, key="im")
    elec = st.number_input("Electricity per day, e-tuktuk (KES)", 0, 1_000, int(D.elec_cost), step=10, key="el")
    e_maint = st.number_input("Maintenance per day, e-tuktuk (KES)", 0, 1_000, int(D.e_maint), step=10, key="em")

with sb.expander("Impact"):
    pump = st.number_input("Petrol price (KES per litre)", 100.0, 400.0, D.pump_price, step=1.0, key="pump")

with sb.expander("Blended finance (placeholders)"):
    blend_target = st.number_input("Target blended funding rate, %", 0.0, 30.0, D.blend_target * 100, step=0.5, key="bt") / 100
    conc_rate = st.number_input("Concessional tranche rate, %", 0.0, 30.0, D.concessional_rate * 100, step=0.5, key="cr") / 100
    stress = st.slider("Stress annual default rate, %", 0.0, 50.0, D.stress_default * 100, 1.0, key="sd") / 100

inp = Inputs(vehicles=vehicles, scale_vehicles=scale_vehicles, loan=float(loan), rate=rate, term=term, scenario=scenario,
             funding_target=f_target, funding_commercial=f_com, funding_usd=f_usd, depreciation=depr,
             default_rate=default_rate, lgd=lgd, admin=admin, fares=float(fares), petrol_cost=float(petrol_cost),
             ice_maint=float(ice_maint), elec_cost=float(elec), e_maint=float(e_maint), pump_price=pump,
             blend_target=blend_target, concessional_rate=conc_rate, stress_default=stress)
fund_rate = m.selected_funding_rate(inp)
pdf, tot = m.portfolio(inp)

# ------------------------------------------------------------------ header
st.title("Mombasa e-tuktuk financing pilot")
st.caption("Concept-stage model: lender returns, funding and blended-finance structure, operator income, and indicative climate impact.")
st.warning("**Concept stage. Not an offer, a quote or a forecast.** No funder, lender or supplier has agreed any term. "
           "Default rate, loss given default, commercial and USD funding rates, depreciation, the concessional tranche and the "
           "stress default rate are placeholders. Results show how the structure behaves, not what will happen.", icon="⚠️")

tabs = st.tabs(["Concept", "Lender result", "Sensitivity", "Blended structure", "Operators", "Pilot vs scale-up", "Assumptions and status"])

# ------------------------------------------------------------------ concept
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Financing needed", kes(inp.vehicles * inp.loan), f"≈ USD {inp.vehicles * inp.loan / inp.kes_per_usd:,.0f}", delta_color="off")
    c2.metric("Lender net surplus, loan life", kes(tot["net_surplus"]), pct(tot["net_pct_of_principal"]) + " of financing", delta_color="off")
    op = m.operator_daily(inp)
    c3.metric("Operator net daily income", kes(op.loc["E-tuktuk, 36-month loan", "Net daily income"]),
              f"petrol: {kes(op.loc['Petrol tuktuk', 'Net daily income'])}", delta_color="off")
    c4.metric("Net CO2e avoided per year", f"{m.impact(inp)['net_co2e_t_year']:.0f} t", "indicative", delta_color="off")
    st.markdown(f"""
### The idea
Mombasa tuktuk operators buy an electric tuktuk on a **{inp.term}-month loan at {pct(inp.rate)} reducing balance**, repaid daily.
The lender is a SACCO or similar institution. To make the loan affordable and the lender whole, the **lender's funding** is
blended: a concessional tranche and a first-loss or guarantee window bring its cost of funds down towards a target of
**{pct(inp.blend_target)}**, in return for measurable climate and livelihood results.

### What this model tests
1. **Does the lender still make money** once defaults, admin costs and funding costs bite? See *Lender result* and *Sensitivity*.
2. **How much concessional support does the structure need?** See *Blended structure*.
3. **Is the loan affordable for operators**, including when fares fall? See *Operators*.
4. **What does scale-up change?** See *Pilot vs scale-up*. Scale multiplies amounts, not unit economics.

### Phasing
A small pilot first. A scale-up of {inp.scale_vehicles} vehicles only follows if the pilot meets targets agreed in advance.
""")
    st.info("The model is linear in fleet size and treats defaults as an expected-value rate. It is a tool for thinking about structure, "
            "not a credit model. See the *Assumptions and status* tab for what would turn each placeholder into evidence.")

# ------------------------------------------------------------------ lender
with tabs[1]:
    st.subheader("Lender result over the loan life")
    st.caption(f"{inp.vehicles} vehicles · funding scenario {inp.scenario} at {pct(fund_rate)} · annual default {pct(inp.default_rate)} · loss given default {pct(inp.lgd, 0)}")
    cols = st.columns(5)
    for col, (label, key) in zip(cols, [("Interest income", "interest_income"), ("Funding cost", "funding_cost"),
                                        ("Admin cost", "admin_cost"), ("Credit loss", "credit_loss"), ("Net surplus", "net_surplus")]):
        col.metric(label, kes(tot[key]))
    st.metric("Annualised credit loss", pct(tot["annual_loss_rate"], 2) + " of balance",
              "concept-paper provisioning allowance: 2.00%", delta_color="off")
    chart = pdf.set_index("month")[["cumulative"]].rename(columns={"cumulative": "Cumulative net surplus (KES)"})
    st.line_chart(chart)
    comp = pdf.melt("month", ["interest_income", "funding_cost", "admin_cost", "credit_loss"], "component", "KES")
    st.altair_chart(alt.Chart(comp).mark_bar().encode(x=alt.X("month:O", title="Month"), y=alt.Y("KES:Q", stack=None),
                    color="component:N", xOffset="component:N", tooltip=["month", "component", alt.Tooltip("KES:Q", format=",.0f")]).properties(height=280),
                    width="stretch")
    with st.expander("Monthly table"):
        st.dataframe(pdf.style.format({c: "{:,.0f}" for c in pdf.columns if c != "month"}), width="stretch")

# ------------------------------------------------------------------ sensitivity
with tabs[2]:
    st.subheader("Lender net surplus: default rate against funding cost")
    st.caption(f"Over the full loan life, {inp.vehicles} vehicles. Red cells are where the lender loses money.")
    sens = m.sensitivity(inp)
    long = sens.reset_index().melt("annual_default_rate", var_name="funding", value_name="surplus")
    long["default"] = long["annual_default_rate"].map(lambda v: pct(v))
    long["fund"] = long["funding"].map(lambda v: pct(v, 0))
    base = alt.Chart(long).encode(x=alt.X("fund:O", title="Funding rate", sort=None), y=alt.Y("default:O", title="Annual default rate", sort=None))
    heat = base.mark_rect().encode(color=alt.Color("surplus:Q", scale=alt.Scale(scheme="redyellowgreen", domainMid=0), legend=None))
    text = base.mark_text(fontSize=12).encode(text=alt.Text("surplus:Q", format=",.0f"), color=alt.value("#111"))
    st.altair_chart((heat + text).properties(height=300), width="stretch")
    st.dataframe(sens.style.format("{:,.0f}"), width="stretch")
    st.caption("Read across a row to see funding cost eat the surplus, and down a column to see defaults eat it. "
               "The gap between cheap and commercial-style funding is the case for concessional or first-loss support.")

# ------------------------------------------------------------------ blended
with tabs[3]:
    st.subheader("Blended finance: subsidy and first-loss sizing")
    b = m.blended(inp)
    c1, c2, c3 = st.columns(3)
    c1.metric("Concessional share of funding needed", pct(b["concessional_share"], 0),
              f"to take {pct(inp.funding_commercial)} down to {pct(inp.blend_target)}", delta_color="off")
    c2.metric("Interest subsidy over the loan life", kes(b["subsidy_kes"]), f"≈ USD {b['subsidy_usd']:,.0f}", delta_color="off")
    c3.metric("Subsidy per vehicle", kes(b["subsidy_per_vehicle"]), pct(b["subsidy_pct_principal"]) + " of financing", delta_color="off")
    c4, c5 = st.columns(2)
    c4.metric(f"First-loss cover at {pct(inp.stress_default, 0)} annual default", kes(b["first_loss_kes"]),
              pct(b["first_loss_pct"]) + " of financing", delta_color="off")
    c5.metric("USD funding: effective KES cost", pct(b["usd_effective_cost"]),
              f"{b['usd_vs_commercial'] * 100:+.1f} points vs commercial KES", delta_color="off")
    st.caption("First-loss figure is expected loss at the stress case, a starting point only. Sizing a real tranche needs a loss distribution "
               "and an unexpected-loss view. All funding inputs here are placeholders.")

# ------------------------------------------------------------------ operators
with tabs[4]:
    st.subheader("Operator economics, KES per working day")
    st.dataframe(op.style.format("{:,.0f}"), width="stretch")
    st.caption("Petrol tuktuk excludes the cost of buying or renting the vehicle, which narrows the gap. "
               "Fares and running costs are working assumptions, not survey results.")
    fs = m.fare_stress(inp)
    fs["Fare change"] = fs["fare_change"].map(lambda v: f"{v * 100:+.0f}%")
    show = fs.rename(columns={"fares": "Daily fares", "e_net_after_repayment": "E-tuktuk net, after repayment",
                              "petrol_net": "Petrol net", "repayment_share_of_income": "Repayment as share of income"})
    st.dataframe(show[["Fare change", "Daily fares", "E-tuktuk net, after repayment", "Petrol net", "Repayment as share of income"]].style.format(
        {"Daily fares": "{:,.0f}", "E-tuktuk net, after repayment": "{:,.0f}", "Petrol net": "{:,.0f}", "Repayment as share of income": "{:.0%}"}),
        width="stretch", hide_index=True)
    st.line_chart(fs.set_index("Fare change")[["e_net_after_repayment", "petrol_net"]].rename(
        columns={"e_net_after_repayment": "E-tuktuk (36-month loan)", "petrol_net": "Petrol tuktuk"}))

# ------------------------------------------------------------------ scale
with tabs[5]:
    st.subheader(f"Pilot ({inp.vehicles}) against scale-up ({inp.scale_vehicles})")
    sc = m.scale_compare(inp)
    fmt = {}
    for idx in sc.index:
        if "%" in idx:
            fmt[idx] = "{:.1%}"
        elif "tonnes" in idx or "litres" in idx:
            fmt[idx] = "{:,.1f}"
        else:
            fmt[idx] = "{:,.0f}"
    shown = sc.copy().astype(object)
    for idx in sc.index:
        for col in sc.columns:
            shown.loc[idx, col] = fmt[idx].format(sc.loc[idx, col])
    st.dataframe(shown, width="stretch")
    st.caption("Scale-up multiplies amounts, not unit economics: net surplus is the same share of financing at both sizes. "
               "Livelihoods are not jobs created: many operators are probably already driving. "
               "Women's economic empowerment and tax revenues are not estimated: there is no data yet.")

# ------------------------------------------------------------------ assumptions
with tabs[6]:
    st.subheader("Assumptions and status")
    st.markdown("Every input is tagged by where it comes from. **Placeholder** means unsourced and must be replaced before anyone relies on an output.")
    rows = []
    for label, field, kind, close in REGISTER:
        val = getattr(D, field)
        rows.append({"Assumption": label, "Default value": f"{val:,.3f}".rstrip("0").rstrip(".") if isinstance(val, float) else str(val),
                     "Status": kind, "How to close it": close})
    reg = pd.DataFrame(rows)
    st.dataframe(reg.style.apply(lambda r: ["background-color: #FFF3B0" if r["Status"] == PLACEHOLDER else "" for _ in r], axis=1),
                 width="stretch", hide_index=True)
    st.markdown("""
#### Disclosure
This is the author's personal, independent concept work. The author is an elected delegate of a Kenyan SACCO, which is a
conflict of interest for any SACCO-related proposal and is stated here. No employer or institution has endorsed or
reviewed this. Nothing here is an offer, a commitment or advice.

#### What would make it referable
A supplier quote, a funder or lender indication on rates, a short Mombasa operator survey, and a named credit professional
reviewing the assumptions. Each is tracked in `docs/ASSUMPTIONS.md` in the repository.
""")
