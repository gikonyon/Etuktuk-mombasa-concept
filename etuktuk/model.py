"""Financial model for the Mombasa e-tuktuk pilot.

Expected-value model, not a stochastic loss model. It is a Python port of the Excel model in
model/ and is tested against it. All outputs depend on the inputs in defaults.py, several of which
are unsourced placeholders.
"""
from __future__ import annotations
from dataclasses import replace
import numpy as np
import pandas as pd
from .defaults import Inputs


def pmt(rate_m: float, n: int, pv: float) -> float:
    """Level monthly installment (positive number)."""
    if n <= 0:
        return 0.0
    if rate_m == 0:
        return pv / n
    return pv * rate_m / (1 - (1 + rate_m) ** -n)


def amortise(pv: float, annual_rate: float, n: int) -> pd.DataFrame:
    r = annual_rate / 12
    inst = pmt(r, n, pv)
    rows, bal = [], pv
    for t in range(1, n + 1):
        interest = bal * r
        principal = inst - interest
        rows.append((t, bal, interest, inst, principal, bal - principal))
        bal -= principal
    return pd.DataFrame(rows, columns=["month", "opening", "interest", "installment", "principal", "closing"])


def selected_funding_rate(i: Inputs) -> float:
    if i.scenario == "A":
        return i.funding_target
    if i.scenario == "B":
        return i.funding_commercial
    return (1 + i.funding_usd) * (1 + i.depreciation) - 1


def hazard(annual_default: float) -> float:
    return 1 - (1 - annual_default) ** (1 / 12)


def total_funder_interest(i: Inputs, funding_rate: float) -> float:
    """Interest paid on one vehicle's funding over the term, level-installment schedule."""
    return pmt(funding_rate / 12, i.term, i.loan) * i.term - i.loan


def portfolio(i: Inputs, vehicles: int | None = None, funding_rate: float | None = None,
              default_rate: float | None = None) -> tuple[pd.DataFrame, dict]:
    n = i.vehicles if vehicles is None else vehicles
    f = selected_funding_rate(i) if funding_rate is None else funding_rate
    d = i.default_rate if default_rate is None else default_rate
    h = hazard(d)
    loan = amortise(i.loan, i.rate, i.term)
    fund = amortise(i.loan, f, i.term)
    t = loan["month"].to_numpy()
    s_start, s_end = (1 - h) ** (t - 1), (1 - h) ** t
    df = pd.DataFrame({
        "month": t,
        "interest_income": n * loan["interest"].to_numpy() * s_end,
        "funding_cost": n * fund["interest"].to_numpy(),
        "admin_cost": n * loan["opening"].to_numpy() * i.admin / 12,
        "defaulted_exposure": n * loan["opening"].to_numpy() * (s_start - s_end),
    })
    df["credit_loss"] = df["defaulted_exposure"] * i.lgd
    df["net_surplus"] = df["interest_income"] - df["funding_cost"] - df["admin_cost"] - df["credit_loss"]
    df["cumulative"] = df["net_surplus"].cumsum()
    principal = n * i.loan
    tot = {k: float(df[k].sum()) for k in ["interest_income", "funding_cost", "admin_cost", "credit_loss", "net_surplus"]}
    tot["principal"] = principal
    tot["net_pct_of_principal"] = tot["net_surplus"] / principal if principal else 0.0
    bal_years = n * loan["opening"].sum() / 12
    tot["annual_loss_rate"] = float(tot["credit_loss"] / bal_years) if bal_years else 0.0
    return df, tot


def gross_margin_paper_basis(i: Inputs, vehicles: int | None = None) -> float:
    """Concept-paper basis: funding at the target rate, no defaults, no admin."""
    n = i.vehicles if vehicles is None else vehicles
    loan = amortise(i.loan, i.rate, i.term)
    return n * (loan["interest"].sum() - total_funder_interest(i, i.funding_target))


def surplus_closed_form(i: Inputs, default_rate: float, funding_rate: float, vehicles: int | None = None) -> float:
    """Net lender surplus over the life, closed form (used for the sensitivity grid)."""
    n = i.vehicles if vehicles is None else vehicles
    h = hazard(default_rate)
    loan = amortise(i.loan, i.rate, i.term)
    t = loan["month"].to_numpy()
    income = (loan["interest"].to_numpy() * (1 - h) ** t).sum()
    funding = total_funder_interest(i, funding_rate)
    admin = loan["opening"].sum() * i.admin / 12
    loss = i.lgd * (loan["opening"].to_numpy() * ((1 - h) ** (t - 1) - (1 - h) ** t)).sum()
    return float(n * (income - funding - admin - loss))


def sensitivity(i: Inputs, defaults=(0.0, 0.025, 0.05, 0.10, 0.15), funding=(0.03, 0.06, 0.09, 0.12)) -> pd.DataFrame:
    data = {f: [surplus_closed_form(i, d, f) for d in defaults] for f in funding}
    return pd.DataFrame(data, index=list(defaults)).rename_axis("annual_default_rate")


def blended(i: Inputs, vehicles: int | None = None) -> dict:
    n = i.vehicles if vehicles is None else vehicles
    com, tgt, con = i.funding_commercial, i.blend_target, i.concessional_rate
    share = 0.0 if com <= tgt else max(0.0, min(1.0, (com - tgt) / (com - con)))
    subsidy = max(0.0, n * (total_funder_interest(i, com) - total_funder_interest(i, tgt)))
    loan = amortise(i.loan, i.rate, i.term)
    h = hazard(i.stress_default)
    t = loan["month"].to_numpy()
    first_loss = n * i.lgd * (loan["opening"].to_numpy() * ((1 - h) ** (t - 1) - (1 - h) ** t)).sum()
    principal = n * i.loan
    usd_cost = (1 + i.funding_usd) * (1 + i.depreciation) - 1
    return {
        "concessional_share": share, "subsidy_kes": subsidy, "subsidy_usd": subsidy / i.kes_per_usd,
        "subsidy_per_vehicle": subsidy / n if n else 0.0, "subsidy_pct_principal": subsidy / principal if principal else 0.0,
        "first_loss_kes": first_loss, "first_loss_pct": first_loss / principal if principal else 0.0,
        "usd_effective_cost": usd_cost, "usd_vs_commercial": usd_cost - com,
    }


def operator_daily(i: Inputs) -> pd.DataFrame:
    a = -pmt(i.rate / 12, 36, i.loan) / i.days_month
    b = -pmt(i.rate / 12, 24, i.loan) / i.days_month
    rows = {
        "Petrol tuktuk": [i.fares, -i.petrol_cost, -i.ice_maint, 0.0],
        "E-tuktuk, 36-month loan": [i.fares, -i.elec_cost, -i.e_maint, a],
        "E-tuktuk, 24-month loan": [i.fares, -i.elec_cost, -i.e_maint, b],
        "E-tuktuk, after loan": [i.fares, -i.elec_cost, -i.e_maint, 0.0],
    }
    df = pd.DataFrame(rows, index=["Fares", "Fuel or electricity", "Maintenance", "Daily loan repayment"]).T
    df["Net daily income"] = df.sum(axis=1)
    return df


def fare_stress(i: Inputs, changes=(-0.30, -0.20, -0.10, 0.0, 0.10)) -> pd.DataFrame:
    rep = pmt(i.rate / 12, 36, i.loan) / i.days_month
    out = []
    for c in changes:
        fares = i.fares * (1 + c)
        pre = fares - i.elec_cost - i.e_maint
        out.append({"fare_change": c, "fares": fares, "e_net_after_repayment": pre - rep,
                    "petrol_net": fares - i.petrol_cost - i.ice_maint,
                    "repayment_share_of_income": rep / pre if pre > 0 else float("nan")})
    return pd.DataFrame(out)


def impact(i: Inputs, vehicles: int | None = None) -> dict:
    n = i.vehicles if vehicles is None else vehicles
    litres_vehicle = i.petrol_cost / i.pump_price
    petrol_t = n * litres_vehicle * i.days_year * i.co2_petrol / 1000
    grid_t = n * i.kwh_day * i.days_year * i.co2_grid / 1000
    return {"litres_per_day": n * litres_vehicle, "petrol_co2_t": petrol_t, "grid_co2_t": grid_t,
            "net_co2e_t_year": petrol_t - grid_t, "net_co2e_t_3y": 3 * (petrol_t - grid_t)}


def scale_compare(i: Inputs) -> pd.DataFrame:
    op = operator_daily(i)
    per_a = op.loc["E-tuktuk, 36-month loan", "Net daily income"] * i.days_year
    per_p = op.loc["Petrol tuktuk", "Net daily income"] * i.days_year
    per_after = op.loc["E-tuktuk, after loan", "Net daily income"] * i.days_year
    cols = {}
    for name, n, tech, chg in [("Pilot", i.vehicles, i.technicians_pilot, i.charging_pilot),
                               ("Scale-up", i.scale_vehicles, i.technicians_scale, i.charging_scale)]:
        _, tot = portfolio(i, n)
        imp, bl = impact(i, n), blended(i, n)
        cols[name] = {
            "Electric tuktuks": n,
            "Financing (KES)": n * i.loan,
            "Financing (USD)": n * i.loan / i.kes_per_usd,
            "Lender net surplus over the loan life (KES)": tot["net_surplus"],
            "Net surplus as % of financing": tot["net_pct_of_principal"],
            "Gross margin, concept-paper basis (KES)": gross_margin_paper_basis(i, n),
            "Operator net income per year while repaying, all operators (KES)": n * per_a,
            "Operator uplift over petrol per year while repaying (KES)": n * (per_a - per_p),
            "Operator net income per year after the loan, all operators (KES)": n * per_after,
            "Livelihoods supported (operators + technicians)": n + tech,
            "Petrol displaced per working day (litres)": imp["litres_per_day"],
            "Net CO2e avoided per year (tonnes)": imp["net_co2e_t_year"],
            "Net CO2e avoided over 3 years (tonnes)": imp["net_co2e_t_3y"],
            "Interest subsidy to reach the target funding rate (KES)": bl["subsidy_kes"],
            "First-loss cover at the stress case (KES)": bl["first_loss_kes"],
        }
    return pd.DataFrame(cols)


def with_(i: Inputs, **kw) -> Inputs:
    return replace(i, **kw)
