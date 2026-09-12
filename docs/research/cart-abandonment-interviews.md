# Research synthesis: cart abandonment interviews

**Researchers:** Jordan Lee, Maya Ortiz  
**n = 11** moderated sessions, Feb 18–27 2026  
**Segment:** US shoppers who started checkout in the last 14 days and did not purchase.

## Method

45-minute sessions. Participants screen-shared the last abandoned checkout when they still had the email. We did **not** show prototype emails; this is problem discovery only.

## Top jobs-to-be-done

1. “Confirm the total before I pay” (8/11)
2. “Park this and finish on my laptop tonight” (6/11)
3. “Check if the brand is legit” (4/11)

## Findings

### Unexpected shipping is the trust break

Seven participants said the shipping line was the moment they left. Four of those had assumed free shipping from the PDP badge “Free shipping over $50,” but their cart was $47. The badge **does not reappear** on checkout.

Quote (P4): “I thought I was done. Then shipping was $8. I closed the tab because I felt tricked, not because $8 is a lot.”

### Payment sheet anxiety

Three participants on mobile Safari described the native payment sheet as “a popup from nowhere.” Two thought Apple Pay would share their full card with the merchant.

Quote (P9): “If you emailed me a link that said guest checkout, I would finish. I am not making an account for $32 of candles.”

### Finish later is real, not a polite excuse

Six people fully intended to return. Four of them could not find the cart on desktop after starting on mobile. Session IDs are device-bound today.

## Implications for the PRD

- Surface the **same shipping quote** in any recovery email. Do not recalculate.
- Deep-link into the **existing checkout session**, not a new cart.
- Offer a **24-hour hold** as a product promise, not a discount.
- Do not lead with a coupon. Several participants said a sudden discount would confirm the brand is “desperate or fake.”

## What we did not hear

Nobody asked for SMS. Two people said they would ignore a third email. Frequency cap belongs in the spec, not as a growth lever to “just send more.”
