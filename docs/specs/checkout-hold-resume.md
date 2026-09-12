# Spec: checkout session hold and resume links

**Engineer partner:** Ravi Patel  
**PRD:** `prd-checkout-recovery-emails.md`  
**Status:** Ready for implementation review

## Session hold

When a checkout is abandoned (payment step viewed, no `order.created` within 20 minutes), write `checkout_holds`:

| Field | Rule |
| --- | --- |
| `session_id` | Existing checkout session |
| `expires_at` | now + 24 hours |
| `shipping_quote_cents` | Frozen quote from the abandoned session |
| `sku_snapshot` | SKUs + quantities at abandon time |

If a SKU’s live stock hits 0 before expiry, the resume page shows an **unavailable** state for that line item. Do not silently drop it.

## Resume URL

Format: `https://shop.example.com/checkout/resume/{session_id}?src=email_e{n}`

- Must work for **guest** users.
- Must restore the frozen shipping quote even if live rates changed.
- `src` is for analytics only; it must not change pricing.

## Email payload from lifecycle service

The email renderer receives:

```
session_id, email, line_items[], shipping_quote_cents, hold_expires_at, inventory_risk: boolean
```

`inventory_risk` is true when any SKU has stock < 8. Only E3 may mention inventory.

## Suppression

Do not enqueue recovery if any of:

- Shopper already has `order.created` for the same cart hash
- Email is on the global suppression list
- Locale is not `en-US`
- Experiment bucket is holdout

E3 is skipped when E1 was opened and not clicked **if** the `suppress_e3_after_open` flag is on. Flag defaults **off** until PM decision (PRD open question).

## Analytics events

- `recovery_email_sent` (email_n, bucket)
- `recovery_email_clicked`
- `checkout_resumed`
- `order_recovered` (attributed if `src` starts with `email_` and order is within 7 days of abandon)

Primary dashboard: recovered GMV / abandoned GMV by bucket.
