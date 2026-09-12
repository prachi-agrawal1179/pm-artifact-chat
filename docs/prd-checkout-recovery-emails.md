# PRD: Checkout recovery emails

**Owner:** Priya Shah (PM, Growth)  
**Status:** Approved for v1  
**Last updated:** 2026-03-12  
**North-star metric:** Recovered checkout GMV

## Problem

12.4% of started checkouts are abandoned after the payment step. Interview synthesis (see `research/cart-abandonment-interviews.md`) shows the top reasons are unexpected shipping cost, distrust of the payment sheet, and “I’ll finish this later.” We send no follow-up today.

## Goals

- Recover **4.0%** of abandoned checkouts within 7 days (baseline: 0%).
- Keep unsubscribe rate **< 0.8%** on the recovery sequence.
- Ship v1 to 20% of abandoned sessions in US English only.

## Non-goals

- SMS or push. Email only for v1.
- Personalized product recommendations in the email body.
- Internationalization beyond US English.

## User stories

1. As a shopper who left after seeing shipping, I want a reminder that includes the **exact shipping quote** I already saw so I do not have to restart.
2. As a shopper who intended to finish later, I want a **24-hour hold** on my cart so inventory does not vanish overnight.
3. As a shopper who distrusts the payment sheet, I want a **guest checkout deep link** that skips account creation.

## Sequence

| Email | Timing | Content |
| --- | --- | --- |
| E1 | T+1 hour | Subject: “Your order is still here.” Body: cart summary + shipping quote + CTA to the same checkout session. |
| E2 | T+24 hours | Subject: “Cart held for 24 more hours.” Body: hold policy + guest checkout link. |
| E3 | T+72 hours | Subject: “Last chance on these items.” Body: inventory risk only if SKU stock < 8. No discount. |

Discounts are **explicitly out of scope**. Finance rejected a 10% win-back coupon because it trained shoppers to abandon.

## Success metrics

Primary: recovered GMV / abandoned GMV in the experiment bucket.  
Secondary: email CTR, checkout completion after click, unsubscribe rate, refund rate of recovered orders (watch for fraud).

Guardrail: refund rate of recovered orders must stay within **+0.3pp** of organic checkout.

## Launch plan

- Week of Apr 6: 5% holdout instrumentation.
- Week of Apr 13: 20% treatment.
- Kill criteria: unsubscribe > 0.8% or refund guardrail breached for 3 consecutive days.

## Open questions

- Legal wants a one-click unsubscribe in E1. Engineering estimates +2 days. **Decision needed by Mar 20.**
- Should we suppress E3 if the shopper opened E1 but did not click? Growth wants suppression; lifecycle wants the full sequence.
