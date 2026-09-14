"""Add the transitive includes recent libstdc++ dropped, to an upstream checkout.

    python -m tools.fix_upstream_includes /content/seasplat_vanilla

**The defect.** Thirteen files across the rasterizer forks and simple-knn use
`uint32_t`, `uint64_t` or `std::uintptr_t` while including only `<iostream>`,
`<vector>` and CUDA headers, and `simple_knn.cu` uses `FLT_MAX` without
`<float.h>`. They relied on libstdc++ pulling `<cstdint>` in transitively.
Recent releases dropped many such includes, so the code stopped compiling on a
toolchain that reports the same CUDA, torch and Python versions as the one it
built on `[docs/reproducibility_notes.md section 5c]`.

This repository fixed its own copies in tree. The upstream checkout is cloned
fresh for every session and is deliberately unpatched, so it carries the defect
and cannot build.

**Why this is not "patching the reference".** The distinction matters, because
the whole value of SS is that it is upstream's code. An added include of a
header the translation unit already depends on introduces no declaration the
compiler did not already resolve, so it cannot change behaviour -- it changes
whether the file compiles at all, and nothing else. That is categorically
different from `tools/instrument_reference.py`, which adds printing to the
densification loop and says in its own docstring that a tree it has touched
must not produce SS numbers.

Every file changed is reported, so the deviation is recorded rather than
assumed. If this ever needs to touch something that is not an include, it
should fail instead.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# The symbol that fails to resolve, and the header that declares it.
NEEDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:std::)?u?int(?:8|16|32|64)_t\b"), "<cstdint>"),
    (re.compile(r"\b(?:std::)?uintptr_t\b"), "<cstdint>"),
    (re.compile(r"\bFLT_MAX\b|\bFLT_MIN\b"), "<float.h>"),
]

SUFFIXES = {".cu", ".cuh", ".h", ".hpp", ".cpp"}


def needs_include(text: str, pattern: re.Pattern, header: str) -> bool:
    if f"#include {header}" in text:
        return False
    return bool(pattern.search(text))


def insertion_point(lines: list[str]) -> int:
    """After the last leading include, or after the licence block."""
    last = -1
    for i, l in enumerate(lines[:80]):
        if l.lstrip().startswith("#include"):
            last = i
    if last >= 0:
        return last + 1
    for i, l in enumerate(lines[:80]):
        if l.strip() and not l.lstrip().startswith(("/*", "*", "//")):
            return i
    return 0


def fix_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    added = [h for pat, h in NEEDS if needs_include(text, pat, h)]
    if not added:
        return []
    lines = text.split("\n")
    at = insertion_point(lines)
    for h in sorted(set(added)):
        lines.insert(at, f"#include {h}")
    path.write_text("\n".join(lines), encoding="utf-8")
    return sorted(set(added))


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m tools.fix_upstream_includes <checkout>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")

    touched: dict[str, list[str]] = {}
    for p in sorted(root.rglob("*")):
        if p.suffix in SUFFIXES and p.is_file():
            added = fix_file(p)
            if added:
                touched[str(p.relative_to(root))] = added

    if not touched:
        print("no missing includes found -- the checkout builds as cloned")
        return 0

    print(f"added includes to {len(touched)} file(s) under {root}:")
    for rel, headers in touched.items():
        print(f"  {rel:<62} {' '.join(headers)}")
    print()
    print("These are additive only. An include of a header the translation unit")
    print("already depends on resolves no new declaration and changes no")
    print("behaviour -- it changes whether the file compiles. The reference is")
    print("otherwise untouched, and this list is the record of the deviation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
