---
section: "3.3.3"
title: "Data Structure and Input–Output Definition"
chapter: 3
action: Retain
evidence: ["run_ledger.json", "results_runs.csv"]
figures: []
tables: ["Table 3.5b"]
citations: []
status: refined
word_count: 664
---

# 3.3.3 Data Structure and Input–Output Definition

**The unit of analysis is a run**: one configuration, on one scene, at one
seed. The campaign contains 120 of them, and every quantity in Chapter IV is
either a property of a run or an aggregate over runs sharing a configuration
and a scene.

Defining the unit precisely matters because two aggregations are used and they
are not interchangeable. A **cell mean** is the mean over three seeds of one
configuration on one scene, and it is what every contrast in Section 3.8.1
combines. A **scene mean** is that same quantity described from the scene's
side. Nothing in this thesis averages across scenes, so no third level exists.

> **[TABLE 3.5b]** *What a run consumes and produces.*

| | Item | Source or destination |
|---|---|---|
| **In** | Undistorted images, camera manifest, initial point cloud | Preprocessing (Section 3.4.5), consumed by hash |
| | Configuration: which mechanisms are enabled, and their settings | Section 3.6.6 |
| | Seed | One of three per configuration and scene |
| **Out** | Trained point cloud | Retained for the first seed only (Section 3.7.5) |
| | Evaluation metrics on held-out and training views | Section 3.7.1 |
| | Cost measures | Section 3.7.2 |
| | Medium scalars, final and through training | Section 3.7.3 |
| | Per-iteration diagnostics, including state at every intervention boundary | Section 3.7.3 |
| | Run manifest: configuration, artefact hashes, environment | Section 3.6.7 |

## Variables

**The independent variables are the three binary mechanism factors** of Section
3.6.1, plus the supplementary contrast of Section 3.5.5 which is handled
separately. Scene is a blocking factor, and seed is the replication index —
neither is a variable whose effect this study estimates, though both appear in
every analysis as sources of variation.

**The dependent variables fall in three groups**, corresponding to the three
evaluation axes: fidelity of the composed image, cost of the representation,
and integrity of the medium model. Sections 3.7.1 to 3.7.3 define each group,
and Section 3.7.5 records which are available at every repeat and which at one.

**No variable is held out for model selection.** There is no validation split
and no hyperparameter is tuned on measured outcomes (Section 3.4.4), so every
configuration value is fixed before a run begins and the dependent variables
are measured once per run rather than selected from.

## A property of the design worth stating here

Every run in the campaign consumes byte-identical preprocessing artefacts for
its scene, verified by hash (Section 3.4.5), and performs the same number of
optimizer steps within its configuration group (Section 3.6.6). Two runs
differing only in seed therefore differ only in the stochastic draws the
training process makes, and two runs differing in configuration differ only in
the mechanisms enabled. That is what allows a difference between cell means to
be attributed to the mechanisms rather than to the data or the schedule, and it
is the structural claim on which every result in Chapter IV depends.

---

## Review log

**Domain Researcher** — The draft defined the run as the unit without
distinguishing the two aggregations used, which is where a reader can go wrong:
a cell mean and a scene mean are the same number described from different
sides, and inventing a third level by pooling across scenes is exactly what
this thesis does not do. → *applied*. Second finding: the variables were not
classified, so blocking factor and replication index read as further
independent variables. → *applied*.

**Supervisor** — The draft was an inventory of files. The subsection's purpose
is to establish that runs differ only in what the design varies, which is the
claim every attribution rests on, and that belongs as its closing statement.
→ *applied*. Devil's advocate: is "differ only in the stochastic draws"
defensible given non-deterministic accumulation? The draws and the accumulation
order both vary; the point is that nothing in the *data* or the *schedule*
varies, which is what the sentence now says.

**Journal Reviewer** — Inputs and outputs were listed without saying which
outputs exist for every run and which for one. → *applied*: the retained point
cloud is marked, with Section 3.7.5 for the full coverage table.
