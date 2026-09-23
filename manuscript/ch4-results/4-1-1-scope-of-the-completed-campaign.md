---
section: "4.1.1"
title: "Scope of the Completed Campaign"
chapter: 4
action: Rewrite
evidence: ["FINDINGS §0", "run ledger"]
figures: []
tables: ["Table 4.1"]
citations: []
status: refined
word_count: 612
---

# 4.1.1 Scope of the Completed Campaign

The results reported in this chapter derive from a single experimental campaign
executed between 15 and 21 September 2026. The campaign comprises ten
configurations evaluated on four underwater scenes with three independent
repeats of each combination, giving 120 training runs. All 120 completed and
all are included; none was discarded after inspection.

The ten configurations consist of the eight cells of the 2³ factorial design
over the three efficiency mechanisms, together with two configurations standing
outside the factorial. The first, denoted SS, is the unmodified upstream
implementation of the underwater baseline, trained and measured on the same
harness as every other configuration. It is the reference against which every
evaluative result in this chapter is reported, and Section 4.2.1 establishes
that it is fit for that role. The second, denoted A0D, is a supplementary
contrast in which the alpha-loss gradient is detached from density control.
Because deterministic initialisation replaces density control entirely, this
mechanism is inert in any configuration containing it; it is therefore measured
against the unmodified configuration alone rather than entered as a fourth
factor, and is reported separately in Section 4.9.

> **[TABLE 4.1]** *Scope of the completed campaign.* Source: FINDINGS §0 and
> the campaign run ledger.

| Property | Value |
|---|---|
| Configurations | 10 (SS, A0–A7, A0D) |
| Scenes | 4 (Curaçao, IUI3 Red Sea, Japanese Gardens, Panama) |
| Repeats per configuration and scene | 3 |
| Training runs | 120, all complete |
| Training iterations per run | 30 000 |
| Effective optimizer steps | 43 000, or 43 400 where simplification is active |
| Accelerator | NVIDIA A100-SXM4-40 GB throughout |
| Total accelerator time | 107 GPU-hours (9–13 h per configuration) |
| Execution window | 15–21 September 2026 |

Results are reported on three axes rather than the two conventional in this
literature. The first is the fidelity of the composed image, measured by peak
signal-to-noise ratio, structural similarity and learned perceptual similarity
on held-out views. The second is cost, measured by primitive count, render rate
and stored size. The third is the integrity of the recovered medium model,
measured by the incidence of attenuation-channel collapse, the physical
plausibility of the learned channel ordering, and the self-consistency of the
restored image across attribute states. The third axis is not conventional and
is the reason this campaign can distinguish configurations that the first two
axes report as equivalent; Sections 4.7 and 4.8 depend on it entirely.

Two details of the accounting bear on the cost comparisons from Section 4.3
onward. First, the number of effective optimizer steps is constant within each
group of configurations: 43 000 for every configuration without simplification
and 43 400 for every configuration with it, the difference being two bursts of
200 medium-only steps that follow the two simplification events. The mechanisms
therefore alter what an iteration costs rather than how many iterations are
performed, and wall-clock differences are attributable to per-iteration cost
rather than to schedule length. Second, four runs required more than one
attempt before completing. Each carried an empty error field, the signature of
a platform disconnection rather than a fault in the run, and each completed on
a subsequent attempt; the completed attempt is the one reported.

The campaign was designed to answer four research questions, stated in Section
1.3.1 and revisited in Section 4.11.1. Sections 4.3 to 4.5 address the first,
concerning each mechanism's effect on cost and fidelity relative to the
reference. Section 4.6 addresses the second, concerning composition. Section
4.7 addresses the third, concerning whether population reduction compromises
the identifiability of the medium model. Section 4.8 addresses the fourth,
concerning whether the fidelity metrics in general use can detect such a
failure at all.

---

## Review log

**Domain Researcher** — The draft described SS as "serving as the reference
control described in Section 4.2.1", which understates its role now that every
evaluative contrast is anchored on it rather than on A0. → *applied*: stated as
the reference against which evaluative results are reported, with 4.2.1
establishing fitness for that role rather than defining it. Second finding: the
draft did not name the three evaluation axes, so a reader met medium integrity
first in Section 4.7 with no warning that it was an axis rather than a
diagnostic. → *applied*: new paragraph, with the explicit note that the third
axis is unconventional.

**Supervisor** — The subsection ended on retried runs, which is housekeeping,
and never told the reader where the chapter is going. → *applied*: closing
paragraph maps sections to research questions. Second finding: "the baseline"
was used for both A0 and SS in adjacent sentences. → *applied*: "the unmodified
configuration" for A0, "the reference" for SS, held consistently.

**Journal Reviewer** — Table lacked a stand-alone caption and a source line.
→ *applied*. Second: "$2^3$" rendered as inline LaTeX in a Markdown deliverable
that will be converted; use the Unicode superscript for consistency with the
rest of the chapter. → *applied*.
