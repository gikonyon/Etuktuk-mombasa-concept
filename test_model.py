"""Reconciliation tests.

1. The Python model reproduces figures in the concept paper.
2. It reproduces the Excel model in model/ (cached values), so the two cannot drift apart silently.
Passing these tests means the arithmetic is consistent. It does not validate the placeholder inputs.
"""
import os
import pytest
from etuktuk.defaults import Inputs
from etuktuk import model as m

I = Inputs()
TOL = 1.0


def test_installment_matches_paper():
    loan = m.amortise(I.loan, I.rate, I.term)
    assert loan["installment"].iloc[0] == pytest.approx(12_712.38, abs=0.01)
    assert loan["interest"].sum() == pytest.approx(77_645.60, abs=0.01)
    assert loan["closing"].iloc[-1] == pytest.approx(0, abs=1e-6)


def test_gross_margin_matches_paper():
    assert m.gross_margin_paper_basis(I) == pytest.approx(1_196_293, abs=TOL)
    assert m.gross_margin_paper_basis(I, 100) == pytest.approx(5_981_465, abs=5)


def test_financing_matches_paper():
    assert I.vehicles * I.loan == 7_600_000
    assert I.scale_vehicles * I.loan == 38_000_000


def test_impact_matches_paper():
    assert m.impact(I)["net_co2e_t_year"] == pytest.approx(49.68, abs=0.01)
    assert m.impact(I, 100)["net_co2e_t_year"] == pytest.approx(248.4, abs=0.05)


def test_operator_economics_match_paper():
    op = m.operator_daily(I)
    assert op.loc["Petrol tuktuk", "Net daily income"] == pytest.approx(900)
    assert op.loc["E-tuktuk, 36-month loan", "Net daily income"] == pytest.approx(970, abs=1)
    assert op.loc["E-tuktuk, after loan", "Net daily income"] == pytest.approx(1500)


def test_base_case_values():
    _, t = m.portfolio(I)
    assert t["interest_income"] == pytest.approx(1_469_734, abs=TOL)
    assert t["funding_cost"] == pytest.approx(356_619, abs=TOL)
    assert t["admin_cost"] == pytest.approx(186_349, abs=TOL)
    assert t["credit_loss"] == pytest.approx(241_756, abs=TOL)
    assert t["net_surplus"] == pytest.approx(685_010, abs=TOL)


def test_closed_form_equals_monthly():
    for d in (0.0, 0.05, 0.15):
        for f in (0.03, 0.09, 0.12):
            _, t = m.portfolio(I, funding_rate=f, default_rate=d)
            assert m.surplus_closed_form(I, d, f) == pytest.approx(t["net_surplus"], abs=0.01)


def test_scale_is_linear():
    _, a = m.portfolio(I, 20)
    _, b = m.portfolio(I, 100)
    assert b["net_surplus"] == pytest.approx(5 * a["net_surplus"], rel=1e-9)


def test_no_default_zero_loss():
    _, t = m.portfolio(I, default_rate=0.0)
    assert t["credit_loss"] == pytest.approx(0, abs=1e-6)


def test_blended_placeholder_case():
    b = m.blended(I)
    assert b["subsidy_kes"] == pytest.approx(871_683, abs=TOL)
    assert b["first_loss_kes"] == pytest.approx(686_119, abs=TOL)
    assert b["concessional_share"] == pytest.approx(0.70)


XLSX = os.path.join(os.path.dirname(__file__), "..", "model", "Mombasa_eTuktuk_Pilot_Financial_Model.xlsx")


@pytest.mark.skipif(not os.path.exists(XLSX), reason="Excel model not present")
def test_python_matches_excel():
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.load_workbook(XLSX, data_only=True)
    _, t = m.portfolio(I)
    assert wb["Portfolio"]["J42"].value == pytest.approx(t["net_surplus"], abs=TOL)
    assert wb["Portfolio"]["E42"].value == pytest.approx(t["interest_income"], abs=TOL)
    assert wb["Portfolio"]["I42"].value == pytest.approx(t["credit_loss"], abs=TOL)
    sc = m.scale_compare(I)
    assert wb["Pilot_vs_Scale"]["C15"].value == pytest.approx(
        sc.loc["Lender net surplus over the loan life (KES)", "Scale-up"], abs=5)
    assert wb["Blended"]["B9"].value == pytest.approx(m.blended(I)["subsidy_kes"], abs=TOL)
    assert wb["Blended"]["B17"].value == pytest.approx(m.blended(I)["first_loss_kes"], abs=TOL)
