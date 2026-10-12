# Design Spec — shopping-cart

- Project: **shopping-cart**
- Spec version: v2 (based on requirements v3)
- Components: 3

## Overview

A FastAPI-style REST service with an in-process cart store, a read-only catalogue client and an order store; SQLite persistence for orders.

## Architecture

Three components behind a thin HTTP layer: cart manager, pricing/total calculator, checkout service.

| Component | Responsibility | Satisfies |
|---|---|---|
| C-01 — cart-manager | Owns cart state per cart token: add, update, remove items; enforces catalogue existence. | REQ-001, REQ-002, REQ-005 |
| C-02 — pricing | Computes the pre-tax total from items and catalogue prices. | REQ-003 |
| C-03 — checkout | Snapshots the cart into a persisted order and empties the cart. | REQ-004 |

## Interfaces


### I-01 — http on C-01

```
POST /v1/cart/items {product_id, quantity}
```

Inputs:

- product_id: string
- quantity: integer >= 1



Outputs:

- 200 with the updated cart view



Errors:

- 404 unknown product_id
- 422 quantity < 1


Satisfies: REQ-001, REQ-005


### I-02 — http on C-01

```
PATCH /v1/cart/items/{product_id} {quantity}
```

Inputs:

- product_id: string
- quantity: integer >= 0



Outputs:

- 200 with the updated cart view; item removed when quantity is 0



Errors:

- 404 product not in cart


Satisfies: REQ-002


### I-03 — http on C-02

```
GET /v1/cart
```

Inputs:

- cart token header



Outputs:

- cart view with items and total (decimal(2) string)



Satisfies: REQ-003


### I-04 — http on C-03

```
POST /v1/cart/checkout
```

Inputs:

- cart token header



Outputs:

- 201 with the created order {id, items, total, created_at}



Errors:

- 409 empty cart


Satisfies: REQ-004


## Data model

- {"description": "In-memory per cart token.", "fields": [{"name": "id", "type": "uuid"}, {"name": "items", "type": "map\u003cproduct_id, quantity\u003e"}], "name": "Cart"}
- {"description": "SQLite table orders.", "fields": [{"name": "id", "type": "uuid"}, {"name": "items_json", "type": "text"}, {"name": "total", "type": "decimal(2)"}, {"name": "created_at", "type": "iso8601"}], "name": "Order"}


## Behaviors


### B-01 — REQ-001

1. Validate quantity >= 1
2. Check product exists in catalogue
3. Increment or insert the cart item
4. Return the cart view


Edge cases:

- cart reaches 100 distinct products -> 422



### B-02 — REQ-002

1. Look up the cart item
2. Set the new quantity; remove the item when 0
3. Return the cart view


Edge cases:

- updating a product not in the cart -> 404



### B-03 — REQ-004

1. Load the cart; reject when empty
2. Compute the total via C-02
3. Insert the order row and commit
4. Empty the cart


Edge cases:

- commit failure -> order not created, cart kept



### B-04 — REQ-006

1. Serve cart reads from memory
2. Serve cart writes with a single lock acquisition


Edge cases:

- lock contention under 50 concurrent shoppers



## Error handling

- {"behaviour": "404, cart unchanged", "case": "unknown product"}
- {"behaviour": "422 with field error detail", "case": "invalid quantity"}
- {"behaviour": "409", "case": "checkout of empty cart"}


## Non-functional requirements

- {"aspect": "performance", "requirement": "p95 under 200 ms at 50 concurrent shoppers (REQ-006)"}
- {"aspect": "durability", "requirement": "orders survive service restart"}


## Test plan

| Test | Verifies | Case |
|---|---|---|
| T-01 | REQ-001 | add P1 qty 2 then P1 qty 1 -> qty 3 |
| T-02 | REQ-002 | set qty 0 -> item removed |
| T-03 | REQ-003 | 10.00 x2 + 5.50 x1 -> total 25.50 |
| T-04 | REQ-004 | checkout -> order persisted, cart empty |
| T-05 | REQ-005 | add unknown product -> 404, cart unchanged |
| T-06 | REQ-006 | 50-shopper load test, p95 < 200 ms |

## Technology choices

- **SQLite for orders** — single-node durability without an external database
- **in-memory carts** — carts are transient; orders are the durable record


## Known issues



- None



## Traceability


| Requirement | Spec elements |
|---|---|
| REQ-001 | B-01, C-01, I-01, T-01 |
| REQ-002 | B-02, C-01, I-02, T-02 |
| REQ-003 | C-02, I-03, T-03 |
| REQ-004 | B-03, C-03, I-04, T-04 |
| REQ-005 | C-01, I-01, T-05 |
| REQ-006 | B-04, T-06 |



