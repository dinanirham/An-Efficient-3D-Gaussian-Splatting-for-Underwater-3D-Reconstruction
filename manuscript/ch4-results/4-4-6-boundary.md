---
section: "4.4.6"
title: "Boundary"
chapter: 4
action: Add
evidence: ["FINDINGS §14", "FINDINGS §0"]
figures: []
tables: []
citations: []
status: refined
word_count: 512
---

# 4.4.6 Boundary

What this section does not establish.

**One budget.** The mechanism was run at a single budget of 200 000 primitives,
applied at two fixed iterations. Nothing here establishes how it behaves at a
larger or smaller budget, at one event rather than two, or on a schedule tied
to convergence rather than to iteration count. This matters more for this
mechanism than for the others, because Section 4.7.2 shows the *size* of the
final representation is not what produces the medium failure — which leaves the
magnitude and the timing of the cut as candidates, and the campaign varied
neither.

**The rate is a rate, not a mechanism.** Five of twelve runs collapsed. The
campaign establishes that this mechanism makes the failure possible where the
reference and the unmodified configuration never produce it, because the
configurations differ by this mechanism alone. It does not establish what
within the mechanism is responsible. The explanation registered before the
campaign was refuted (Section 4.7.3) and no replacement is claimed.

**The medium-only intervals cannot be separated from the pruning.** Every
configuration containing this mechanism also contains the short medium-only
optimisation intervals that follow each event, and the campaign contains no
configuration that prunes without them. Whether those intervals cause the
medium's excursion or merely provide the iterations during which it happens is
untestable with these runs (Section 4.7.5).

**No collapsed and intact pair at the retained repeat.** Full point clouds were
kept for the first repeat only. No cell has both a collapsed and an intact run
at that repeat, so every rendered comparison between the two outcomes differs
in configuration as well as in outcome, and Figure 4.13's caption says so.

**Resolution, and what unresolved means.** The mechanism's pixel-metric effect
against the reference is `UNRESOLVED` on all four scenes. That is a statement
about three repeats against this corpus's dispersion, not a measurement of
zero. The perceptual effect resolves on all four and is the more secure result
of the two.

**Four scenes from one corpus.** As for every mechanism in this chapter, the
acquisition style is common to all four scenes and the behaviour under wider
baselines, more views, or different water is untested. The one scene that
produced no collapse is also the scene with the least coherent medium fit
(Section 4.2.4), and whether those two facts are related is not established.

**Render rate at these populations only.** The fitted slope between population
and frame rate is measured over the configurations this campaign ran, whose
final populations span roughly 130 000 to 4 300 000 primitives. Extrapolating
the relationship below or above that range is not supported.

---

## Review log

**Domain Researcher** — The draft did not state that budget and schedule were
both fixed, which is the first limitation a referee would raise given that
Section 4.7.2 rules out final size as the cause. → *applied*, and placed first
with the reason it matters more here than elsewhere. Second finding: the
population range over which the frame-rate relationship was fitted was
unstated. → *applied*.

**Supervisor** — Two entries duplicated Section 4.3.6 nearly verbatim.
→ *applied*: both rewritten to what is specific to this mechanism, with the
general corpus limitation kept short and the rest left to Section 4.12. Second:
the entry on the medium-only intervals originally read as a minor caveat; it is
a confound the design cannot remove. → *applied*: stated as untestable with
these runs.

**Journal Reviewer** — `UNRESOLVED` appeared without its meaning in a
subsection that may be read alone. → *applied*, with the note that the
perceptual result is the more secure of the two. Second: the no-matching-pair
limitation was stated in Figure 4.13's caption but not in the text.
→ *applied*.
