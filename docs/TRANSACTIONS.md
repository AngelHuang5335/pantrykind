# Transaction contracts

Interactive household POSTs start a transaction and lock the household before
reading mutable rows. Membership and the kitchen timezone are refreshed inside
that boundary. Stock services enforce current active membership independently
of HTTP middleware. Invitation acceptance follows the same parent-first order.

PostgreSQL locks a household row; unrelated kitchens do not share that row lock.
SQLite first performs a no-op household update, acquiring its database write lock
before business reads. SQLite still supports only one writer. Connection failures
and lock timeouts are errors, and a client should retry an uncertain operation
with its original request ID rather than inventing another one.

| Operation | Atomic effects | Replay contract |
| --- | --- | --- |
| Stock movement | Conditional quantity change and audit event | Same batch, actor, kind, quantity and note return the original event, including after archiving |
| Cook recipe | Availability check, FEFO deductions, stock events and cook receipt | Household lock precedes replay lookup; identical requests wait and return the first receipt |
| Receive purchase | New dated batch, restock event, remaining list quantity and purchase receipt | Full payload must match; receipt survives clearing its source shopping entry |
| Deliver inbox | Fenced lease check, notification creation and job acknowledgement | Unique job reference plus one transaction prevents duplicate notifications |

Quantity validation is shared by stock, list and purchase services; invalid,
non-finite, excessive or over-precision amounts fail before writes. Conditional
updates also prevent overdraw and cumulative overflow. Cooking locks batches in
primary-key order, then allocates their quantities in first-expiring order.
Metadata forms carry a timestamp revision and reject saves after the batch changes.

Shopping checkmarks only manage the checklist; they do not create stock. Only
explicit purchase submission does so. Planning does not reserve food. Existing
opening quantities remain opening balances; purchases added through the new flow
have explicit restock ledger events. Legacy cook receipts retain nullable actors;
new receipts record the initiating user.

Reminder work uses two-minute leases, token fencing, bounded retry delays and a
terminal dead state. The in-app transport commits delivery and acknowledgement
together. These guarantees do not describe hypothetical external email delivery.
See [reminder operations](REMINDERS.md) for cancellation and recovery behavior.
