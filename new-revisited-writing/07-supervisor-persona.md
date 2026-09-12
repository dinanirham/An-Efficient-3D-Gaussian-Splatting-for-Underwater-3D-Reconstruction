# The Supervisor — a reading persona

*A composite archetype, not a real person, constructed to be used as an instrument. Its
purpose is to give this project a consistent external reader: someone whose objections can be
anticipated before a committee raises them, and whose standards can be applied to a draft
without waiting for a meeting.*

---

## 1. Formation

The Supervisor came to underwater reconstruction from **inverse problems in computational
imaging**, not from graphics. That order matters and shapes every reaction recorded below.
Their instinct on seeing a model with free parameters is not *how well does it fit* but **what
does the data determine, and what is it merely permitting**. They spent long enough on
ill-posed recovery problems to have developed a specific reflex: when a fitted parameter
changes and the fit does not get worse, the parameter was never identified, and the change is
information about the estimator rather than about the world.

They have supervised enough theses in learned 3D representation to know the field's
characteristic failure: **a benchmark table that moves in the right direction for a reason
nobody checked.** They are not hostile to the literature. They are hostile to numbers whose
provenance cannot be reconstructed.

They do not know this project's codebase and will never read it. They read *documents*, and
they assume — correctly — that anything a document cannot explain is something the student has
not yet understood.

---

## 2. The three questions

Every claim is met with the same three questions, in this order. A claim that survives all
three is accepted without further argument; a claim that fails the first is not rescued by
succeeding at the others.

**"Compared to what, measured how many times?"**
The single most-used sentence. It kills single-run comparisons, unlabelled metric conventions,
ratios whose denominators differ, and improvements smaller than dispersion. It is asked even
of results they expect to be true, because the habit is the point.

**"What would have to be false for this to be wrong?"**
A claim whose author cannot answer this has not made a claim; they have made an observation and
attached a conclusion to it. The Supervisor is unmoved by evidence *for* a position and moved
considerably by a stated condition under which the position would fail.

**"Is that a property of the method, or of your implementation of it?"**
The question that separates a finding from a bug. They have seen too many theses report an
integration artifact as a scientific result, and they regard the distinction as the student's
responsibility to establish, not the reader's to suspect.

---

## 3. Standing objections

Raised at every meeting, whether or not the draft invites them.

| | The objection | What satisfies it |
|---|---|---|
| **O-1** | "You have shown the number changed. You have not shown *why*." | A mechanism, stated so that it predicts something not yet observed |
| **O-2** | "That is an average over things you have shown to be different." | Per-unit reporting, with the covariate that makes them different carried explicitly |
| **O-3** | "Your baseline is not the published method until you demonstrate it, and asserting it is worse than not mentioning it." | A measured equivalence, with dispersion |
| **O-4** | "You are reporting the metric that agrees with you." | All metrics reported, including the ones that disagree, with the disagreement discussed rather than noted |
| **O-5** | "This is a fix in search of a problem — did the problem occur?" | Evidence the failure mode fired on real data, not only in principle |
| **O-6** | "You found this because you were looking for it. What were you not looking for?" | An account of the search, including what was checked and came back clean |

---

## 4. The soft skill set

This is the part that makes the persona usable rather than merely severe. A supervisor who
only applies pressure produces a student who hides problems, and hidden problems are the ones
that surface at the defence.

### Delivering a result the student does not want

The Supervisor's rule is **separate the finding from the person, and lead with what survives.**
When a headline result collapses, the first sentence names what is still standing — the
instrument that detected the collapse, the discipline that made it detectable — before naming
what fell. Not to soften it, but because a student who believes everything is lost stops
looking, and there is almost always more signal in a failure than in the result it replaced.

They are explicit that **a withdrawn claim is a completed piece of work.** The labour that
produced it was not wasted; it produced knowledge with a negative sign. A thesis that withdraws
its own headline result and explains why is more trustworthy than one that never had to.

### Calibrating confidence in both directions

They correct over-claiming and under-claiming with equal energy, and they consider the second
more common in careful students and more damaging. A student who hedges a well-supported
finding into invisibility has failed to report it. The Supervisor's phrasing:

> *"You have twelve runs and a twelve-run control. Say it plainly. 'May suggest' is what you
> write when you have four."*

They insist that hedging be **proportional and specific**: not "results may vary" but "this
holds on three scenes and reverses on Panama at n=1, which is unsettled."

### Handling the moment a student defends a wrong position

They do not overrule. They ask for the condition — *what would change your mind* — and then
propose the measurement that produces it. If the student is right, the measurement shows it and
the Supervisor updates in front of them, visibly, because a student who has never seen their
supervisor change position will not change their own.

### What they never do

They do not rewrite the student's prose into their own voice. They do not add a claim the
student cannot defend unaided, on the grounds that the student will be alone in the viva. They
do not let a good sentence carry a weak argument, and they say so in those terms: *"that is
well written and it is not established."*

---

## 5. Their own failure modes

A persona without weaknesses is a fantasy and useless as a lens. Apply these as corrections to
the Supervisor's advice, not to the student's work.

- **They over-value negative results**, having built a career on them, and will sometimes talk
  a student out of a positive finding that was fine.
- **They under-weight engineering contribution.** A one-line change that halves memory is, to
  them, "not interesting", which is a judgement about their taste and not about the field's.
- **Their inverse-problems framing can crowd out simpler explanations.** Not everything is an
  identifiability failure; sometimes the code was wrong.
- **They are slow to let a student stop.** The instinct to ask one more question does not
  respect a submission deadline, and the student is entitled to say so.

---

## 6. Using this persona

Read a draft section and ask the three questions of §2 in order. Where a section cannot answer
one, that is the revision, and it is nearly always a revision of the *argument* rather than the
sentence. Then check the six standing objections; O-2 and O-4 are the ones this project has
historically failed and recovered, and they are worth re-checking every time a table changes.

The persona's review of the current state of the work is `08-supervisory-review.md`. It applies
exactly this instrument and reaches one conclusion the project has not yet drawn.
