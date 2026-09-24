---
section: "3.7.1"
title: "Reconstruction Fidelity"
chapter: 3
action: Refine
evidence: ["results_runs.csv", "CD register"]
figures: []
tables: []
citations: ["Wang et al., 2004", "Zhang et al., 2018"]
status: refined
word_count: 712
---

# 3.7.1 Reconstruction Fidelity

Three fidelity metrics are recorded for every run: peak signal-to-noise ratio,
structural similarity (Wang et al., 2004) and learned perceptual similarity
(Zhang et al., 2018). All three are computed on the held-out views of Section
3.4.4, against the captured images as ground truth.

**All three are computed on the composed image.** This is the quantity the
estimator renders after the medium model has been applied (Section 3.1.1), and
it is the only quantity in the decomposition for which ground truth exists. The
restored image and the two medium maps are not evaluated against any reference,
because none is available in this corpus. Section 3.7.3 describes what is
recorded about them instead, and Section 4.8.3 reports what this limitation
costs.

## Conventions that affect the numbers

**Peak signal-to-noise ratio is recorded in two forms.** The pooled form
computes the mean squared error over all channels together and converts once;
the per-channel form converts each channel separately and averages the results.
The two differ, and mixing them across a comparison would introduce a
discrepancy unrelated to any mechanism. This thesis reports the pooled form
throughout, and Chapter IV's tables are pooled values.

**The perceptual backbone is recorded per run rather than assumed.** Learned
perceptual similarity varies with the network it is computed from, and a figure
quoted without its backbone is not comparable with another. The backbone is
written into every run's results row, so a reader can confirm that every value
in a comparison was produced the same way.

**Training-set metrics are recorded alongside held-out metrics** for all three
measures. They are not reported as results — a fidelity figure on data the
model was fitted to is not an estimate of reconstruction quality — but they are
retained as a diagnostic. Section 4.8.1 uses them to establish that the
insensitivity of the fidelity metrics to medium-model failure is not an
artefact of evaluating on held-out views: the training metrics behave the same
way.

## What these metrics can and cannot support

The two fidelity metrics measure different properties and disagree about this
corpus in ways that matter. Section 3.3.2 shows they rank the four scenes
differently, and Chapter IV reports mechanisms that are neutral on one and
resolved-adverse on the other. **Where they disagree, this thesis reports the
disagreement rather than selecting the metric that resolves it**, and the
mechanism sections state both.

The choice of three metrics rather than one is not redundancy. Peak
signal-to-noise ratio responds to radiometric agreement and is insensitive to
the loss of high-frequency texture that Section 4.4.4 identifies as spatial
reorganisation's characteristic artefact. Learned perceptual similarity
responds to that texture and is the metric on which every mechanism in this
study shows a cost. Structural similarity moves least of the three and is
reported for completeness; it resolves on almost nothing in this campaign,
which is itself worth recording.

A property of the evaluation set bounds all three and is stated here rather
than left to the limitations. Each scene mean rests on three or four held-out
images (Section 3.4.4), and those images differ in difficulty by 6.65 to 11.25
dB within a single run. Because every configuration is scored on the same fixed
views, comparisons between configurations are unaffected. What is affected is
any reading of a scene mean as the typical quality achieved on that scene, and
Section 3.7.5 states the reporting consequence.

---

## Review log

**Domain Researcher** — The draft named three metrics without stating that all
three are computed on the composed image, which is the single most important
thing about them in this thesis. → *applied*: stated immediately, with what is
not evaluated and why. Second finding: the pooled-versus-per-channel
distinction was not recorded, though both are computed and mixing them would
introduce a spurious discrepancy. → *applied*, with the convention this thesis
uses.

**Supervisor** — The draft presented three metrics as standard practice. Saying
what each is *for* — and that structural similarity resolves on almost nothing
here — turns a list into a justified choice. → *applied*. Devil's advocate:
should a metric that resolves nothing be reported at all? Yes, and reporting
that it resolves nothing is part of the result; omitting it after the fact
would be selective.

**Journal Reviewer** — The perceptual backbone was not mentioned, and a learned
metric without its backbone is not comparable across papers. → *applied*:
recorded per run. Second: training-set metrics appear in the results table and
the draft did not say why they exist. → *applied*: retained as a diagnostic,
with the use Section 4.8.1 makes of them.
