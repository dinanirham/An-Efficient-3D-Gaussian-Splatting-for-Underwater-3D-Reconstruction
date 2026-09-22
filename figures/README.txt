METHODOLOGY FIGURES — vector and raster, for the thesis document

Each figure is here twice. Use the SVG wherever the target accepts it: it is
resolution-independent and its text stays text (selectable, searchable, and
re-typeable by a typesetter). Use the PNG where SVG is awkward — some Word
builds, some templates, a quick slide.

  figure-0-optimisation-loop.svg  /  .png     837 x 1119 pt   1675 x 2237 px
  figure-1-pipeline.svg           /  .png    1115 x 4867 pt   2231 x 9734 px
  figure-2-schedule.svg           /  .png     900 x  250 pt   1800 x  500 px

PNGs are rendered at 2x the SVG's own size. Figure 1 is very tall by nature;
in a portrait thesis page it will want either a full page of its own or a
landscape/rotated placement.

--------------------------------------------------------------------------
WHAT THESE ARE

The same three figures as the methodology page:
  new-revisited-writing/figures-methodology.html   (artifact source)
  https://claude.ai/artifact/BqdkonmDqJsFYcVTcWJfKG (live page)
Figures 0 and 1 come from the mermaid sources figure-0-highlevel.mmd and
figure-1-pipeline.mmd; figure 2 is hand-written SVG inside the page.

--------------------------------------------------------------------------
HOW THEY WERE EXPORTED, AND WHY IT IS NOT THE SAME AS THE WEB PAGE

_export-harness.html is the page that produced them: serve this directory
over http (python -m http.server), open it in a browser next to a copy of
the page source named src.html and an npm install of mermaid@11.16.1, and it
renders all three. Three deliberate differences from the live page:

1. htmlLabels: false. On the web, mermaid puts node labels in <foreignObject>
   — HTML inside SVG. Browsers draw it; Word, Inkscape, LaTeX toolchains and
   most SVG importers draw an empty box instead. With htmlLabels false the
   labels are real <text>, which every consumer understands. This is the
   single change that makes the files usable outside a browser.

2. HTML entities are decoded before rendering. The page's diagram sources
   write "&lpar;" and "&lt;" because the HTML parser decodes them on the way
   in; with htmlLabels false nothing decodes them and they would print
   literally ("exp&lpar;-B_att.Z&rpar;"). The harness decodes them first.

3. Arial, not IBM Plex Sans. mermaid sizes every box from the text metrics of
   the font in use at render time, so a figure laid out in a webfont the
   reader does not have comes out with clipped labels. Arial is on every
   Windows and macOS machine, so the measuring font and the viewing font are
   the same one. Figure 2's monospace rows use Consolas / Courier New for the
   same reason. The live page keeps IBM Plex, so the exports are very
   slightly wider-set than the web version. Nothing else differs.

--------------------------------------------------------------------------
IF YOU EDIT A FIGURE

Edit the source, never these files: the .mmd for figures 0 and 1, or the
<svg> block inside figures-methodology.html for figure 2. Then republish the
artifact, rebuild the standalone copy
(python new-revisited-writing/build_standalone.py), and re-export here.

Figure 2's M3 label read "quantisation-aware training · straight-through"
until 2026-09-22; at 11 px it was wider than the 213 pt box it sits in and
overran on both sides, on the live page as well as in export. Shortened in
the source, so the page and these files agree.
