"""Tests for the manuscript scaffold generator.

    python tools/verify_manuscript_scaffold.py

The generator turns `THESIS.md` §22.8 into one Markdown file per subsection. The thing that matters most is T4: it must never overwrite a file
that already holds drafted prose, because the scaffold is regenerated whenever
the structure changes and the drafting runs for months alongside it.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from make_manuscript_scaffold import (  # noqa: E402
    Entry,
    parse_structure,
    render_stub,
    slug,
    write_scaffold,
)

ROOT: Path = Path(__file__).resolve().parent.parent.parent
STRUCTURE: Path = ROOT / "THESIS.md"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if condition else 'FAIL'}  {name}")
    if not condition:
        FAILURES.append(f"{name}: {detail}")


def t1_slug() -> None:
    check("T1 slug strips emphasis and punctuation",
          slug("**Baseline Validation**") == "baseline-validation",
          slug("**Baseline Validation**"))
    check("T1 slug collapses runs and trims",
          slug("Collapsed Versus Intact Strata") == "collapsed-versus-intact-strata")
    check("T1 slug handles an en dash",
          slug("Storage–Fidelity Relationship") == "storage-fidelity-relationship",
          slug("Storage–Fidelity Relationship"))


def t2_parses_every_row() -> None:
    entries = parse_structure(STRUCTURE)
    check("T2 every numbered row is parsed", len(entries) == 164, f"got {len(entries)}")
    chapters = sorted({e.chapter for e in entries})
    check("T2 all five chapters present", chapters == [1, 2, 3, 4, 5], str(chapters))


def t3_four_and_five_column_tables() -> None:
    """Chapter IV's table omits the Content column; the rest carry it."""
    entries = parse_structure(STRUCTURE)
    ch4 = [e for e in entries if e.chapter == 4]
    hit = [e for e in ch4 if e.number == "4.8.1"]
    check("T3 chapter IV parses without a Content column", len(hit) == 1)
    if hit:
        check("T3 chapter IV evidence read from the right column",
              hit[0].evidence == "§8", repr(hit[0].evidence))
    ch1 = [e for e in parse_structure(STRUCTURE) if e.number == "1.1.4"]
    check("T3 chapter I keeps its Content column", len(ch1) == 1)
    if ch1:
        check("T3 chapter I evidence is the last column",
              ch1[0].evidence == "§9", repr(ch1[0].evidence))


def t4_never_clobbers_drafted_prose() -> None:
    """The scaffold is regenerated as the structure moves; drafting is not."""
    entries = [Entry(chapter=4, number="4.8.1", title="Collapsed Versus Intact Strata",
                     action="Add", evidence="§8", content="")]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        write_scaffold(entries, out)
        target = next(out.rglob("4-8-1-*.md"))
        drafted = target.read_text(encoding="utf-8") + "\n\nReal prose written later.\n"
        target.write_text(drafted, encoding="utf-8")

        created, skipped = write_scaffold(entries, out)
        check("T4 a second run writes nothing", created == 0, f"created {created}")
        # The chapter index is skipped alongside the stub, so two, not one.
        check("T4 a second run reports both skips", skipped == 2, f"skipped {skipped}")
        check("T4 drafted prose survives regeneration",
              target.read_text(encoding="utf-8") == drafted)


def t5_stub_carries_its_metadata() -> None:
    e = Entry(chapter=4, number="4.7.3", title="The Registered Explanation and Its Refutation",
              action="Add", evidence="§5b", content="")
    text = render_stub(e)
    check("T5 stub opens with front matter", text.startswith("---\n"))
    check("T5 stub carries the section number", 'section: "4.7.3"' in text)
    check("T5 stub starts at status draft", "status: draft" in text)
    check("T5 stub carries the evidence", "§5b" in text)
    check("T5 stub blocks completion with a marker", "[TODO]" in text)
    check("T5 stub carries the review log", "## Review log" in text)


def t6_sections_become_directories_not_files() -> None:
    entries = parse_structure(STRUCTURE)
    numbers = {e.number for e in entries}
    check("T6 section rows are kept", "4.2" in numbers)
    check("T6 subsection rows are kept", "4.2.1" in numbers)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        write_scaffold([e for e in entries if e.chapter == 4], out)
        files = list(out.rglob("*.md"))
        check("T6 a file exists per subsection, plus one index per chapter",
              any(f.name == "README.md" for f in files))
        check("T6 no file is written for a bare section number",
              not any(f.name.startswith("4-2-baseline") for f in files))


def main() -> int:
    print("manuscript scaffold")
    for fn in (t1_slug, t2_parses_every_row, t3_four_and_five_column_tables,
               t4_never_clobbers_drafted_prose, t5_stub_carries_its_metadata,
               t6_sections_become_directories_not_files):
        fn()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} failure(s):")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
