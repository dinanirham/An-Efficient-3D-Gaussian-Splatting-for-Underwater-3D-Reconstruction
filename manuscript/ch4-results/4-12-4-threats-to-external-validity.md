---
section: "4.12.4"
title: "Threats to External Validity"
chapter: 4
action: Add
evidence: ["FINDINGS §14", "FINDINGS §2b", "FINDINGS §11"]
figures: []
tables: ["Table 4.28"]
citations: []
status: refined
word_count: 727
---

# 4.12.4 Threats to External Validity

The question this subsection addresses is which of the chapter's findings would
be expected to hold outside the conditions under which they were measured.

**One scene behaves differently from the other three, in five respects, and it
is the scene on which every per-scene claim must be checked before it is
generalised.**

> **[TABLE 4.28]** *Observations attaching to IUI3 Red Sea.* Each is reported
> in the section named; they are collected here because their co-occurrence on
> one scene is itself an observation.

| Observation | Section |
|---|---|
| Every mechanism's largest perceptual cost falls here: +0.059, +0.082 and +0.028, each at 20 standard errors or more | 4.3.1, 4.4.1, 4.5.1 |
| No simplification run loses a channel in six attempts, where the other three scenes collapse at a seed-conditioned rate | 4.7.1 |
| The simplification × quantisation interaction does not resolve, where it resolves on the other three | 4.6.3 |
| The initialisation × quantisation perceptual interaction takes the opposite sign to the other scenes | 4.6.4 |
| The fitted attenuation spectrum is inverted in direction while the backscatter spectrum is not — the only scene on which the two halves of the medium model disagree | 4.2.4 |
| Quantisation's pixel-metric effect does not replicate across campaigns | 4.10.1 |

The scene's acquisition is consistent with a poorly constrained
geometry–medium decomposition: it has the most training views of the four, at
25, and those views were taken consecutively along a reef wall, which is the
worst-conditioned camera pairing in the corpus. That is an association across
six observations on one scene, not a demonstration, and the campaign varied
neither view count nor camera baseline and so cannot test it.

The consequence for external validity is specific. Findings that hold on all
four scenes — the mechanisms' count reductions, the perceptual cost of spatial
reorganisation, the insensitivity of the fidelity metrics — are supported
across the corpus including its anomalous member. Findings that hold on three
scenes and not on this one should be read as conditional on scene
conditioning, not as general.

**The medium collapse is the finding whose generality is least established, and
the reason is unexpected.** It occurs on three of four scenes and not on the
fourth — and the fourth is the one where the medium fit is least coherent to
begin with. A reader might reasonably expect the poorly constrained scene to be
the most vulnerable; it is the only one immune. Whether that is because a fit
that was never well determined has nothing to lose, or for some other reason,
is not established. Until it is, the collapse rate of nine in twenty-four
should be read as a rate over this corpus rather than as a property of the
mechanism transferable to other scenes.

**The corpus is one dataset with one acquisition style.** Nothing here
establishes behaviour in different water types, at different turbidity, at
wider camera baselines, or with acquisition geometries other than those
represented. The image formation model the estimator assumes is itself an
approximation, and this campaign does not test the conditions under which that
approximation holds.

**Two findings are expected to generalise beyond the underwater setting, for
structural rather than empirical reasons.** The first is the methodological
result of Section 4.8.3: an objective that scores a composition constrains the
composition and not its factors, which applies to any estimator claiming a
decomposition. The second is the interaction of Section 4.6.2: pruning to an
absolute budget cannot compose multiplicatively with a mechanism that reduces
the entering population, which is arithmetic and not a property of scenes.
Neither is demonstrated outside this corpus, and both are argued from structure
rather than observed elsewhere.

**One finding is expected not to generalise as stated.** The 2.72-fold
compression of Section 4.5.2 follows from an attribute layout with
spherical-harmonic degree zero and would differ under any other layout. It is
arithmetic, and the arithmetic is specific to this configuration.

---

## Review log

**Domain Researcher** — The draft treated the anomalous scene as a nuisance.
The most interesting thing about it is that it is immune to the collapse while
being the least coherent fit, which inverts the expectation a reader would
form. → *applied*: own paragraph, with the expectation named and the
alternative readings left open. Second finding: the draft did not distinguish
findings supported across the whole corpus from those holding on three scenes.
→ *applied*.

**Supervisor** — The draft said nothing about what *would* generalise, which
makes an external-validity section purely defensive. → *applied*: two findings
argued to generalise on structural grounds and one argued not to, each with the
reason. Devil's advocate: is claiming structural generalisation without
external evidence overreach? It is flagged as argued rather than observed, in
the same sentence.

**Journal Reviewer** — The six observations were described in prose and could
not be checked against their sections. → *applied*: tabulated with section
references. Second: the acquisition detail was stated as though explanatory.
→ *applied*: named as an association across six observations on one scene,
with the untested variables identified.
