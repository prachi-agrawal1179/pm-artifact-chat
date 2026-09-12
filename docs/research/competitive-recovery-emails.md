# Competitive teardown: public recovery-email patterns

**Author:** Alex Kim (PM, Growth)  
**Date:** 2026-03-01  
**Method:** Mystery-shopped three public storefronts. This is an internal memo based on **public checkout and email behavior**, not leaked docs.

## Competitor A — Harbor & Co. (DTC home)

- Sends **one** email at ~45 minutes. Subject includes the product name.
- Body restates **itemized shipping**. CTA is “Resume checkout.”
- No discount. No third email observed over 5 days.
- Guest checkout link works without login. Session expired after ~36 hours in our test.

Implication: Harbor treats recovery as **logistics reminder**, not a promo channel. Matches our research (discount = distrust).

## Competitor B — Northbeam Supply (marketplace-style)

- Three-email sequence at 30m / 12h / 3d.
- E2 always includes **10% off** with code NORTH10.
- E3 adds free shipping regardless of cart value.
- Unsubscribe link is below the fold and easy to miss.

Implication: Northbeam optimizes for short-term conversion. Public reviews mention “coupon after I abandon,” which is the exact failure mode Finance flagged.

## Competitor C — Lumen Pets (subscription + one-off)

- No recovery email if the shopper has an active subscription (suppression).
- One-off customers get a single email at T+6 hours with a **cart hold countdown**.
- Help article (public): holds last 24 hours; after that the cart is a snapshot, not live inventory.

Implication: Hold + countdown is the pattern we should copy. Suppression for existing subscribers is a v2 candidate, not v1.

## What we will not copy

- Automatic coupons (Northbeam).
- More than three emails.
- Login-walled resume links.

## Recommendation

Harbor’s single reminder is too timid given our 12.4% abandon rate after payment. Lumen’s hold + countdown plus Harbor’s honest shipping line is the v1 shape. See PRD sequence E1–E3.
