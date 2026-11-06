"""Inputs and the assumptions register.

Every input is tagged with where it comes from. "placeholder" means it is NOT sourced
from a lender, supplier or operator and must be replaced before anyone relies on an output.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Inputs:
    # Pilot terms (concept paper)
    vehicles: int = 20
    scale_vehicles: int = 100
    loan: float = 380_000.0
    rate: float = 0.125
    term: int = 36
    days_month: int = 24
    kes_per_usd: float = 130.0
    # Funding scenarios
    scenario: str = "A"             # A concessional target, B commercial KES, C USD with depreciation
    funding_target: float = 0.03    # concept paper target
    funding_commercial: float = 0.10  # placeholder
    funding_usd: float = 0.07       # placeholder
    depreciation: float = 0.05      # placeholder
    # Credit and cost
    default_rate: float = 0.05      # placeholder (annual share of loans defaulting)
    lgd: float = 0.40               # placeholder (share of balance lost on default)
    admin: float = 0.015            # concept paper design assumption (150 bps)
    # Operator economics (working assumptions)
    fares: float = 1_800.0
    petrol_cost: float = 750.0
    ice_maint: float = 150.0
    elec_cost: float = 250.0
    e_maint: float = 50.0
    # Impact (working assumptions)
    pump_price: float = 180.0
    days_year: int = 288
    co2_petrol: float = 2.31
    kwh_day: float = 10.0
    co2_grid: float = 0.10
    # Blended finance
    blend_target: float = 0.03
    concessional_rate: float = 0.0  # placeholder
    stress_default: float = 0.15    # placeholder
    # Support (to confirm)
    technicians_pilot: int = 4
    technicians_scale: int = 20
    charging_pilot: int = 2
    charging_scale: int = 20


PAPER, PLACEHOLDER, WORKING = "Concept paper", "Placeholder", "Working assumption"

# (label, field, kind, how to close it)
REGISTER = [
    ("Fleet size, pilot and scale-up", "vehicles", PAPER, "Agree with partners"),
    ("Loan per vehicle (KES)", "loan", WORKING, "Written supplier quote, all-in with battery and telemetry"),
    ("Operator loan rate, reducing balance", "rate", PAPER, "Confirm with the lending institution"),
    ("Loan term (months)", "term", PAPER, "Confirm with the lending institution"),
    ("Concessional target funding rate", "funding_target", PAPER, "A target someone must fund: needs a funder indication"),
    ("Commercial KES funding rate", "funding_commercial", PLACEHOLDER, "Borrowing quotes from two or three lenders"),
    ("USD funding rate", "funding_usd", PLACEHOLDER, "Indicative term sheet from a DFI or impact lender"),
    ("Expected KES depreciation p.a.", "depreciation", PLACEHOLDER, "A view backed by forward rates or published forecasts"),
    ("Annual default rate", "default_rate", PLACEHOLDER, "Repayment history of comparable transport-sector loans"),
    ("Loss given default", "lgd", PLACEHOLDER, "Resale and immobilisation terms; recovery experience"),
    ("Administration cost, % of balance p.a.", "admin", PAPER, "Costing from the lending institution"),
    ("Daily fares and running costs", "fares", WORKING, "Short survey of Mombasa e-tuktuk and petrol operators"),
    ("Petrol price per litre", "pump_price", WORKING, "Current regulator pump price for Mombasa"),
    ("Emission factors, kWh per day", "co2_petrol", WORKING, "A recognised methodology and independent verification"),
    ("Concessional tranche rate", "concessional_rate", PLACEHOLDER, "What a funder would actually offer"),
    ("Stress default rate", "stress_default", PLACEHOLDER, "A loss distribution, not a single number"),
    ("Technicians and charging points", "technicians_pilot", WORKING, "Sized with the supplier and agreed"),
]
