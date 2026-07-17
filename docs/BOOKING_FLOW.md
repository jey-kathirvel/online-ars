# Booking and payment flow

## Availability synchronization

ERP and the online application use the same PostgreSQL booking and room-allocation tables. Overlapping `RESERVED`, `CONFIRMED` and `CHECKED_IN` allocations block a room in both applications. Expired online holds do not block availability.

## Online lifecycle

```text
Availability search
  → no room hold
Pay full amount
  → Razorpay order created
  → booking RESERVED for 10 minutes
Payment captured and verified
  → booking CONFIRMED
Payment not completed before expiry
  → booking CANCELLED / PAYMENT EXPIRED
  → assigned room released
```

The server verifies the Razorpay signature, order ID, captured status, INR currency and exact full amount. Partial payment is not accepted online; ERP staff bookings may still accept partial payment.

## Pricing

- Room rate × room count × billed 24-hour days
- Two occupants are included per room
- Third occupant: ₹500 × room count × billed days
- GST: 5% on room and extra-occupant subtotal
- Razorpay order: complete GST-inclusive total

Any duration beyond a complete 24-hour block is rounded up to the next billed day.
