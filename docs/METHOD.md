# Method

An **expected-value** model. It is not a stochastic loss model, so it sizes expected loss, not unexpected loss.

**Operator loan.** Level monthly installment on a reducing balance: `installment = P·r / (1 − (1 + r)^−n)`, with `r = rate / 12` and `n` the term in months.

**Defaults.** A fixed share of loans defaults each month: `h = 1 − (1 − d)^(1/12)` for annual default rate `d`. The share still performing after `t` months is `(1 − h)^t`.

**Lender result over the loan life, for `N` vehicles.**
- Interest income = `N · Σ interest_t · (1 − h)^t`
- Funding cost = `N ·` interest on a level-installment funding schedule at the selected funding rate. The lender repays its funder in full on schedule whatever the operators do.
- Admin cost = `N · Σ opening_t · admin / 12`
- Credit loss = `N · LGD · Σ opening_t · ((1 − h)^(t−1) − (1 − h)^t)`
- Net surplus = income − funding − admin − credit loss

**Blended structure.**
- Concessional share needed = `(commercial − target) / (commercial − concessional)`, bounded between 0 and 1.
- Interest subsidy = extra funder interest at the commercial rate against the target rate, over the term.
- First-loss cover = expected credit loss at the stress default rate.

**Operators.** Net daily income = fares − fuel or electricity − maintenance − daily loan repayment. The fare stress table moves fares and keeps costs fixed.

**Impact.** Petrol displaced = daily petrol spend ÷ pump price. CO2e avoided = petrol burned × emission factor, less grid electricity × grid factor. Indicative only.

## Reconciliation
`tests/test_model.py` checks that the Python model reproduces the concept paper (installment, total interest, gross margin of KES 1,196,293 at 20 vehicles, CO2e) and the Excel model in `model/`. Passing tests mean the arithmetic is consistent. They do not validate the placeholder inputs.
