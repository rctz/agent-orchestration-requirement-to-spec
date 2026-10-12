# Design Spec — temp-conv

- Project: **temp-conv**
- Spec version: v1 (based on requirements v2)
- Components: 1

## Overview

A single-file Python command-line tool that parses one numeric argument and prints the converted temperature, with strict input validation.

## Architecture

One stateless component: parse, validate, convert, print.

| Component | Responsibility | Satisfies |
|---|---|---|
| C-01 — converter | Parse the CLI argument, validate it is a finite number, apply the conversion formula and print the result with two decimals. | REQ-001, REQ-002 |

## Interfaces


### I-01 — cli on C-01

```
temp-conv <value> [--to {f|c}]
```

Inputs:

- value: decimal string
- --to: optional target unit, default f



Outputs:

- converted temperature printed with two decimals



Errors:

- exit code 2 with stderr message when value is not a finite number


Satisfies: REQ-001, REQ-002, REQ-003


## Data model

- {"description": "Transient value; nothing is persisted.", "fields": [{"name": "input_value", "type": "decimal"}, {"name": "direction", "type": "enum", "values": ["c2f", "f2c"]}], "name": "Conversion"}


## Behaviors


### B-01 — REQ-001

1. Parse the positional argument as a decimal
2. Validate the value is finite
3. Compute F = C * 9/5 + 32
4. Print the result with two decimals


Edge cases:

- negative values
- values below absolute zero are still converted numerically



### B-02 — REQ-002

1. Parse the positional argument as a decimal
2. Validate the value is finite
3. Compute C = (F - 32) * 5/9
4. Print the result with two decimals


Edge cases:

- negative values



### B-03 — REQ-003

1. Attempt float() conversion of the argument
2. On failure print 'error: <argument> is not a number' to stderr
3. Exit with code 2


Edge cases:

- NaN and infinity inputs are rejected as invalid



## Error handling

- {"behaviour": "stderr message + exit code 2", "case": "non-numeric argument"}


## Non-functional requirements

- {"aspect": "performance", "requirement": "a single conversion completes in under 50 ms"}


## Test plan

| Test | Verifies | Case |
|---|---|---|
| T-01 | REQ-001 | temp-conv 0 -> prints 32.00 |
| T-02 | REQ-001 | temp-conv 100 -> prints 212.00 |
| T-03 | REQ-002 | temp-conv 32 --to c -> prints 0.00 |
| T-04 | REQ-003 | temp-conv abc -> exit code 2, stderr message |

## Technology choices

- **Python 3.13 standard library only (argparse)** — no external dependencies for a small CLI


## Known issues



- None



## Traceability


| Requirement | Spec elements |
|---|---|
| REQ-001 | B-01, C-01, I-01, T-01, T-02 |
| REQ-002 | B-02, C-01, I-01, T-03 |
| REQ-003 | B-03, I-01, T-04 |



