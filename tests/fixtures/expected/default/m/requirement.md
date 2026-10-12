# Requirements — shopping-cart

- Project: **shopping-cart**
- Document version: v3
- Size class: M
- Requirements: 6 total, 5 must

## Goal

A REST shopping-cart service: add items, update quantities, remove items and check out with a persisted order.

## Users

- Shoppers via a web frontend
- Operators reading orders

## Scope

### In scope

- Cart item add/update/remove
- Cart total calculation
- Checkout that creates an order
- Product catalogue is read-only input

### Out of scope

- Payment processing
- User accounts and authentication
- Product catalogue management

## Requirements


### REQ-001 — Add item to cart

- Kind: functional
- Priority: must

A shopper can add a product to their cart with a positive quantity; adding an existing product increases its quantity.

Acceptance:

- Given an empty cart when adding product P1 qty 2 then the cart contains P1 with quantity 2
- Given a cart with P1 qty 2 when adding P1 qty 1 then the cart contains P1 with quantity 3


### REQ-002 — Update item quantity

- Kind: functional
- Priority: must

A shopper can set a cart item's quantity to any value >= 1; setting 0 removes the item.

Acceptance:

- Given a cart with P1 qty 2 when setting qty 5 then the cart shows P1 qty 5
- Given a cart with P1 qty 2 when setting qty 0 then the cart no longer contains P1


### REQ-003 — Cart total

- Kind: functional
- Priority: must

The cart exposes a total: the sum of unit price times quantity over all items, before tax.

Acceptance:

- Given P1 (10.00) qty 2 and P2 (5.50) qty 1 when requesting the total then the total is 25.50


### REQ-004 — Checkout creates an order

- Kind: functional
- Priority: must
- Refs: D-02

Checkout converts the cart into a persisted order with a unique id, the items, the total and a timestamp, then empties the cart.

Acceptance:

- Given a cart with items when checking out then an order exists with those items and the cart is empty


### REQ-005 — Unknown product rejected

- Kind: functional
- Priority: must

Adding a product id that is not in the catalogue fails with a 404 and does not change the cart.

Acceptance:

- Given product PX not in catalogue when adding PX then the API returns 404 and the cart is unchanged


### REQ-006 — Cart response time

- Kind: nonfunctional
- Priority: should

Cart read and write operations respond within 200 ms at 50 concurrent shoppers.

Acceptance:

- Given 50 concurrent shoppers when measuring cart operations then p95 latency is under 200 ms


## Data


### Cart

- `id` (uuid) — assigned at first add

- `items` (list of CartItem) — at most 100 distinct products



### CartItem

- `product_id` (string) — must exist in catalogue

- `quantity` (integer) — >= 1 while in cart



### Order

- `id` (uuid) — unique

- `items` (list of CartItem) — snapshot at checkout

- `total` (decimal(2)) — equals cart total at checkout





Formats: money values are decimal(2) strings


## Assumptions

- **A-01**: Prices come from the product catalogue; the cart never stores prices.
- **A-02**: One cart per shopper session, identified by a cart token header.


## Decisions

- **D-01** (Q-01): No payment processing in v1 — _user_

- **D-02** (Q-02): Checkout empties the cart immediately — _system_default_expired_ (chosen by system: question expired without answer)



## Glossary

- **Catalogue**: The read-only product master data.
- **Cart token**: Opaque header value identifying one cart.


## Open items



- None
