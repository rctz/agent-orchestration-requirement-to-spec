# Requirements — temp-conv

- Project: **temp-conv**
- Document version: v2
- Size class: S
- Requirements: 3 total, 3 must

## Goal

A command-line tool that converts temperatures between Celsius and Fahrenheit.

## Users

- CLI users on POSIX systems

## Scope

### In scope

- Convert Celsius to Fahrenheit
- Convert Fahrenheit to Celsius
- Single CLI invocation per conversion

### Out of scope

- Kelvin support
- Graphical interface
- Batch conversion of files

## Requirements


### REQ-001 — Convert Celsius to Fahrenheit

- Kind: functional
- Priority: must

Given a Celsius value, the tool prints the equivalent Fahrenheit value rounded to two decimals.

Acceptance:

- Given 0 C when converting then the output is 32.00
- Given 100 C when converting then the output is 212.00


### REQ-002 — Convert Fahrenheit to Celsius

- Kind: functional
- Priority: must

Given a Fahrenheit value, the tool prints the equivalent Celsius value rounded to two decimals.

Acceptance:

- Given 32 F when converting then the output is 0.00
- Given 212 F when converting then the output is 100.00


### REQ-003 — Clear error on invalid input

- Kind: nonfunctional
- Priority: must
- Refs: D-01

When the argument is not a finite number, the tool prints an error message to stderr and exits with a non-zero code.

Acceptance:

- Given the argument 'abc' when running the tool then stderr contains an error and the exit code is 2


## Data


### Conversion

- `input_value` (decimal) — parses as a finite number

- `direction` (enum c2f|f2c) — default c2f





Formats: <value> [--to f|c]


## Assumptions

- **A-01**: Input arrives as a single CLI argument.


## Decisions

- **D-01** (Q-01): No Kelvin support in v1 — _system_default_expired_ (chosen by system: question expired without answer)



## Glossary

- **CLI**: Command-line interface.


## Open items



- None
