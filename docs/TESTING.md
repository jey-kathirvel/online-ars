# Acceptance testing

## Automated

```powershell
python -m pytest -q
```

## Website

- Verify home, rooms, Explore, contact and footer links.
- Verify responsive header, transparent peacock logo and mobile navigation.
- Open every booking button and confirm the iframe modal loads.
- Confirm direct `/book` fallback remains usable.

## Availability

- Create an ERP staff booking and confirm the room disappears online for the overlapping period.
- Start an online payment and confirm ERP shows `RESERVED` with a countdown.
- Confirm an online hold blocks staff selection.
- Let a hold expire and confirm both systems release the room.

## Pricing and payment

- Test one, two and three occupants per room.
- Confirm the third occupant adds ₹500 per room/day before GST.
- Confirm a partial 24-hour block rounds up.
- Complete a Razorpay test payment and verify `CONFIRMED`, `PAYMENT CAPTURED`, full advance and an ERP payment record.
- Dismiss checkout and verify expiry produces `CANCELLED / PAYMENT EXPIRED` with the guest mobile number visible in ERP.
