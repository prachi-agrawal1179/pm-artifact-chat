# Decision log: checkout recovery v1

## D-14 — No win-back coupon (2026-03-04)

**Decision:** v1 emails must not include percentage off, free shipping codes, or gift-with-purchase.  
**Why:** Finance model showed a 10% coupon would make recovered orders **margin-negative** on the median cart ($41). Research also found discounts increase distrust.  
**Owner:** Priya Shah. **Approver:** CFO staff meeting notes 2026-03-04.

## D-15 — 24-hour hold, not 48 (2026-03-07)

**Decision:** Inventory hold is 24 hours.  
**Why:** Supply chain will not reserve popular SKUs for 48h. Lumen Pets’ public help center documents a 24h hold; we match that user expectation.  
**Revisit:** After 30 days of hold utilization data.

## D-16 — US English only (2026-03-08)

**Decision:** Ship to `en-US` sessions only.  
**Why:** Copy and legal review are not staffed for DE/FR this quarter. Internationalization is a v1.5 follow-up, not a silent expansion.

## D-17 — Legal unsubscribe in E1 (pending)

Legal requested one-click unsubscribe in the first email. Engineering: +2 days. Decision deadline **Mar 20**. Until decided, spec includes the link because the cost of a slip is higher than a two-day slip.
