---
section: "4.7.5"
title: "The Re-Identification Burst"
chapter: 4
action: Add
evidence: ["FINDINGS §5e", "diagnostics CSVs"]
figures: ["figure-4-10-attenuation-trajectory"]
tables: []
citations: []
status: refined
word_count: 592
---

# 4.7.5 The Re-Identification Burst

Each pruning event in this implementation is followed by 200 optimisation steps
in which only the medium parameters are updated and the geometry is held fixed.
The interval was added as a remedy: after a large change to the population, the
medium model is given an opportunity to re-fit against the new geometry before
ordinary training resumes. This subsection reports what it actually does.

The interval behaves as designed in the narrow mechanical sense. The geometric
diagnostics recorded at the end of the interval are identical to those recorded
immediately after pruning, on 48 of 48 runs at both events: the burst moves no
geometry. Whatever it changes, it changes only in the medium parameters.

**What it changes is the direction of the damage.** Section 4.7.4 established
that pruning itself leaves the attenuation coefficients untouched, and that
they move during the interval that follows. This is the stronger negative
result: the burst is not merely failing to restore the medium model, it is the
interval in which the medium model falls. On every large cut the attenuation
loss is expressed here, and in six of the nine collapses this is where a
channel crosses zero — at iteration 15 001, one step past the first pruning
event.

The re-identification interval is therefore where the damage is written, not
where it is repaired. Two hundred medium-only steps against a geometry that has
just lost nine tenths of its primitives do not recover the parameters; they
allow the optimiser to move the parameters rapidly to whatever now fits, and on
these runs what now fits is a coefficient at or below zero.

**The campaign cannot say whether the interval causes this or merely hosts
it.** Every configuration containing spatial reorganisation also contains the
interval, so there is no contrast between pruning with the burst and pruning
without it. Whether the same fall would occur over the next 200 ordinary
iterations, with geometry also free to move, is untested by this design. The
distinction matters practically: if the interval causes the fall, removing it
is a candidate remedy; if it merely hosts a fall that would happen regardless,
removing it would change nothing and might make matters worse by denying the
medium any opportunity to re-fit.

What is established is narrower and still worth stating. **Two hundred
medium-only steps against the cut geometry are not a remedy.** The mechanism
they were intended to provide — re-identification of the medium after a
population change — does not occur at the cut sizes this campaign produces
without deterministic initialisation. Section 5.4 carries the contrast that
would separate cause from host: a configuration running the same pruning
schedule with the interval removed, which is a single additional cell and the
cheapest unanswered question in the design.

---

## Review log

**Domain Researcher** — The draft said the burst "fails to restore" the medium,
which understates the finding. It is the interval in which the loss is
expressed, which is a different and stronger claim, and the 48-of-48 geometric
evidence is what makes it attributable to the interval rather than to ordinary
training. → *applied*, with the mechanical result stated first so the
attribution is clear. Second finding: the practical consequence of the
cause-versus-host ambiguity was absent. → *applied*: what each answer would
imply for a remedy.

**Supervisor** — The draft presented the confound as a caveat at the end. It is
the subsection's main limitation and belongs in the body, stated as something
the design cannot do rather than as a footnote. → *applied*, bolded. Devil's
advocate: does naming the missing cell overstate how easy the fix is? It is one
additional configuration on an existing schedule, which is why it is described
as the cheapest unanswered question rather than a trivial one.

**Journal Reviewer** — "Six of the nine" recurred from Section 4.7.1 without
the iteration that makes it specific. → *applied*: 15 001, one step past the
first event. Second: the missing contrast needed a destination.
→ *applied*: Section 5.4.
