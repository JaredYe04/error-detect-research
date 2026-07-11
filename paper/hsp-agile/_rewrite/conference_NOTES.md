# Conference rewrite NOTES



**Staging:** `_rewrite/conference_main.tex`  

**Live copy:** `hsp-agile-conference/main.tex` (identical)  

**Date:** 2026-07-11



## What was removed (meta / defensive)



- “Decision framework (not a better generator)” and similar anti-claim framing

- Intro “Threats up front” FAQ block → folded into Discussion *Limitations*

- Discussion “What not to claim” checklist → factual limitation sentences

- Conclusion “Remember:” / reviewer-takeaway tone

- “hygiene” jargon → “matched budget” / “equal-$K$ Conf. ranking”

- “stress-test only” slogan cluster → “near-ceiling ranking context” (stated once)

- Archive-only failure-taxonomy figure and complexity heatmap (page budget)

- Latency + Pareto figure pair (numbers kept in prose from AUTHORITATIVE_NUMBERS)

- Vendor TBD row and ethics/contact template digression (one-line NDA note retained)



## What was restructured



- **Abstract** aligned with long-form `front/abstract.tex` vignette + Accept definition;

  claim order per brief/user: Accept lead → E6 (+7.7 pp / others) → E2 FAR → C4 B2 default

- **Intro:** concept (Accept) first, then primary catch-all vignette (with $S_3$↔$S_8$ bridge),

  secondary ordering marked, contributions C3/C2/C4 without Scope:/Non-claim tags

- **Approach:** catch-all JSON as primary worked step; ordering example marked secondary

- **Results:** E6 → equal-$K$/E1 context → E2 → C4 → external; captions tightened

- **Discussion:** Practice + Limitations + Reproducibility (no rebuttal FAQ)

- **Conclusion:** Accept spine restated; three evidence bullets without defensive hedges



## Number fixes (vs prior conference cut)



- E1 wall-clock: B2 **9.6 s**, M **10.5 s** (was swapped in prose)

- All primary claims verified against `AUTHORITATIVE_NUMBERS.md`:

  E6 86.9/79.1/+7.7, 14/4/102, CI [2.3,13.6], p=0.018, 14/14 others;

  E2 PDR/FAR 95.0/5.0 vs 91.2/8.8;

  equal-$K$ 100.0 vs 97.5 (+2.5; 3/0/117);

  E1 84.2/98.3/100.0; E12 B2 100% / M 99.7%;

  external n=31/28/48/35; gemini pooled +26.5; field NL-only +28.0



## Labels preserved



- Kept: `tab:rw`, `alg:sgdp`, `tab:corpus`, `fig:e6`, `tab:e6`, `tab:field-conf`,

  `tab:defect-map`, `tab:e1`, `fig:prev`, `fig:overlap`, `tab:deploy`, `sec:ext`, `tab:ext`

- Dropped floats (no longer referenced): `fig:complex`, `fig:latency`, `fig:pareto`, `fig:fail`



## Page budget (target 8–9 / ≤10)



| Block | Est. |

|-------|------|

| Abstract + keywords | 0.35 |

| Intro | 0.9 |

| Related + Table rw | 0.7 |

| Approach + alg | 1.4 |

| Setup + corpus | 0.7 |

| Results (core figs/tables) | 3.2 |

| Discussion + Conclusion | 0.8 |

| References | ~1.0 |

| **Total** | **~8.5–9.5** |



Trim levers if over 10: drop `tab:field-conf` (keep +28 pp in prose) or `fig:overlap`

(keep non-monotone sentence). Do not cut E6 bar or E2 prevention figure.

