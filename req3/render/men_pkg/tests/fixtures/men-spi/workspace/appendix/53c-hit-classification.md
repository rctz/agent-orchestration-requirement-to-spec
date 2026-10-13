Here are the four hits classified, and the folds they require:

## A — §4.5 mutation row 13 (proving test)
Context: "non-writable-dir case AND pre-existing read-only target case (both
at-open failures: E-WRITE, target byte-untouched — D-46; ...)"
Required fold: this is the D-46/OSError context, but the sweep wants the
scoping explicit. The sub-case names E-WRITE (the OSError class) so the
byte-untouched claim is already class-correct; add "(D-46/OSError forms;
the at-open MemoryError class is D-57/R-6)" — NO, that would be redundant:
E-WRITE IS the OSError class. This is a sweep false-positive: the sentence
scopes by E-WRITE, which is OSError-only by catalog definition (§6.3).
Disposition: teach the sweep that 'e-write' counts as OSError scoping.

## B — §5.3 S-14(c)
Context: "an error before S5 leaves it byte-untouched (REQ-008/010...)"
Required fold: "before S5" = pre-open, i.e. the D-43/D-46 domain. The at-open
MemoryError is an S5-stage failure, but "error before S5" excludes everything
that happens in S5 including the at-open window. Sweep false-positive: the
phrase "before S5" is a pre-open scoping. Teach the sweep "before s5".

## C — §11 coverage paragraph, D-46 index entry
Context: "an at-open failure reports E-WRITE directly and leaves the output
target byte-untouched whether absent or pre-existing (read-only target in a
writable dir survives...)"
Required fold: THIS ONE IS REAL. The D-46 index sentence says "an at-open
failure" unqualified, and D-46's trigger class is every-exception-after-open;
its at-open story as written now overstates — D-57 carved the MemoryError
at-open out of the byte-untouched rule. The v11 pattern (SR6-F-04 class)
requires folding the qualifier here too. Fix the SPEC: add "for the OSError
forms (the at-open MemoryError class of D-57 is the recorded R-6 exception)"
to the D-46 index entry.

## D — §5.1 post-diagram note
Context: "The output file can exist only after WRITTEN; every path into
REPORTING leaves the filesystem untouched on the output side (§4.5's
compensation is the one cleanup)."
Required fold: THIS ONE IS REAL. The at-open MemoryError/KI path is a path
into REPORTING(memory) that leaves a 0-byte file — the sentence as written
is the same absolute-claim class F-01 flagged in the pre-open edge. Fix the
SPEC: scope the sentence "on the output side ... byte-state untouched EXCEPT
the recorded at-open residue (R-6, D-54/D-57)".
