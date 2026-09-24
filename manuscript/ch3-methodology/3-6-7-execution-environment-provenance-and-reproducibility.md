---
section: "3.6.7"
title: "Execution Environment, Provenance and Reproducibility"
chapter: 3
action: Add
evidence: ["FINDINGS §0", "run_ledger.json"]
figures: []
tables: []
citations: []
status: refined
word_count: 748
---

# 3.6.7 Execution Environment, Provenance and Reproducibility

The campaign ran on a single accelerator type, an NVIDIA A100-SXM4-40 GB,
across a continuous window from 15 to 21 September 2026, for 107.0 GPU-hours
in seven sequential stages (Section 3.2). No configuration change was made
during the window, and no stage overlapped another.

## What is recorded, and what it establishes

Campaign state is held in a durable ledger rather than in the driving process,
because the compute environment terminates sessions long before a stage
completes and a process that dies takes its record with it. The ledger records,
per run: the configuration, scene and seed; the stage; start and finish times;
wall-clock duration; the accelerator; the number of attempts; and the output
location. It is the source for the completeness accounting of Section 4.1.1 and
for the stage table of Section 3.2.

Each run additionally records the hashes of the preprocessing artefacts it
consumed (Section 3.4.5), so the claim that every configuration trained on
identical data is checkable rather than asserted.

## What is not recorded, and what that costs

**The per-run commit identifier is empty for all 120 runs.** The collection tool
read a field that the configuration manifest does not write. The manifest does
record the implementation state — the information exists in each run
directory — but the column that was intended to carry it into the results table
is blank.

The consequence is stated precisely because it is narrower than it first
appears. The claim that all runs share one implementation state rests on the
ledger's continuous execution window and on the worker log, rather than on a
recorded identifier. That is weaker evidence: the ledger establishes that the
runs executed in one unbroken window by one worker, which makes a mid-campaign
change unlikely, but it could not have detected one.

Two further consequences are recorded rather than repaired. The same defect
affects an earlier campaign whose comparison with this one is reported in
Section 4.10, so a non-replication between them cannot be attributed to a named
code change — and a sampled manifest from that earlier campaign records an
uncommitted working tree, so even a recorded identifier would not have
described the code that ran. The defect has been located and corrected, and the
field populates in subsequent collections, which serves future work and does
nothing for the campaign reported here.

## What reproducibility is available

**Bit-exact reproduction is unattainable and is not claimed** (Section 3.6.3):
the rasteriser's backward pass accumulates atomically, and floating-point
addition is not associative. What is available is reproduction at the level of
dispersion — a re-execution should produce results within the repeat
dispersion this campaign measures — and Section 4.10.1 reports an internal
replication against an earlier campaign that meets that standard on perceptual
similarity for all sixteen comparisons and on primitive count for the
deterministic mechanism to three significant figures.

That replication is internal: two campaigns by the same author with overlapping
code. It establishes stability under re-execution and not independent
reproduction, and a systematic error present in both would replicate perfectly.
Section 4.12.2 states this rather than letting the word "replication" carry
more than it should.

The artefacts required for an external attempt are the four preprocessing
outputs per scene with their hashes (Section 3.4.5), the configuration for each
cell, the intervention schedule of Section 3.6.6, and the analysis plan of
Section 3.6.4. The one thing an external party cannot recover from this
campaign is the exact implementation state, for the reason given above.

---

## Review log

**Domain Researcher** — The draft reported the missing commit identifier as a
defect without distinguishing what the fallback evidence can and cannot do. A
referee will ask precisely that. → *applied*: the ledger makes a mid-campaign
change unlikely but could not have detected one. Second finding: the draft did
not say that the information exists in the run directories and only the results
column is blank, which materially changes how serious the defect is.
→ *applied*.

**Supervisor** — The draft ended on the defect, leaving a reader with the
impression that nothing about the campaign is reproducible. The available
standard — reproduction within measured dispersion — is a real claim and the
internal replication partly meets it. → *applied*, with the honest limit that
the replication is internal. Devil's advocate: is "reproduction at the level of
dispersion" a weaker standard adopted for convenience? It is the only standard
available given atomic accumulation, and Section 3.6.3 gives the reason rather
than asserting it here.

**Journal Reviewer** — The artefacts an external party would need were never
enumerated, in the subsection nominally about reproducibility.
→ *applied*: four items, each located, with the one irrecoverable thing named.
Second: the accelerator was given generically here while Section 4.1.1's scope
table names the model, which would read as an inconsistency between chapters.
→ *applied*: named here, matching that table; Section 3.2 carries the stage
timings and does not repeat it.
