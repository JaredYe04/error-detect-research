# Harsh CCF-B Critic + Mentor Audit — Staging Rewrite

**Auditor role:** CCF-B journal critic + Mentor guidelines enforcer  
**Scope:** `paper/hsp-agile/_rewrite/` (abstract, ch01–ch09, industrial_case) vs `REWRITE_BRIEF.md` + `AUTHORITATIVE_NUMBERS.md`  
**Date:** 2026-07-11  

---

## Overall verdict

**Conditional accept after language/scope polish — not yet camera-ready.**

Claim spine and primary numbers (E2 FAR 5.0%/8.8%, E6 +7.7 pp / 14/4/102, equal-$K$ +2.5 pp) are largely correct and consistently cited. The rewrite successfully removed most reviewer-FAQ slogans. Remaining blockers are (1) **defensive “Scope: / not a claim” residue** that still reads like rebuttal, (2) **vignette discontinuity** (3-scenario intro vs S8 hard-task coding; industrial case mislabeled as catch-all), (3) a **compile-breaking stray `)`** in Ch.2, and (4) Mentor slips (burying contributions under caveats; “Takeaways/remember”; “hygiene” overuse; “motivational” theorem framing).

**Numbers card:** FAR/PDR authoritative values appear correctly in abstract, Ch.1, Ch.4 table, Ch.7, Ch.8, Ch.9. No 0.14/0.22 FAR found. E1/E12 framing is honest (B2 seed-stable; M not universal Conf. crown).

**After Critical/Major language fixes in this pass:** staging should be structurally sound for promotion review; remaining Minors are polish.

---

## Abstract

| Sev | Finding |
|-----|---------|
| **Major** | “Equal-$K$ **hygiene**” is checklist jargon (brief: use sparingly). Prefer matched-budget / equal-$K$ Conf. ranking. |
| Minor | Opens well (vignette → Accept → evidence). FAR/PDR defined mid-paragraph after first use of the acronyms in spirit—acceptable but could define one line earlier. |
| Minor | “Artifacts released.” is abrupt; fine for thesis abstract. |
| OK | E2 5.0%/8.8%, E6 numbers, 14 others / 0 ordering, equal-$K$ 100.0/97.5, B2-default deployment — match AUTHORITATIVE_NUMBERS. |

---

## Chapter 1 — Introduction

| Sev | Finding |
|-----|---------|
| **Critical** | Contributions C3–C4 still use **“Scope: we do not claim / not uniqueness / not a production CI”** — forbidden defensive pattern (brief: state as *limitations* or *deployment guidance*, not rebuttal tags). |
| **Major** | Headline contributions paragraph: “not a claim that mode~M always wins mean Conf.” — same violation; buries C3 under anti-claim. |
| **Major** | Mentor: C3 opens with evidence and caveats before restating the acceptance idea cleanly (Abstract-then-Concrete partially violated in the enumerate). |
| Minor | “equal-$K$ hygiene” again. |
| OK | Primary OTHERWISE→Review / Pass vignette solid; secondary tax clearly marked; E6 win profile preview consistent with card. |
| OK | FAR 5.0%/8.8%; E6 86.9/79.1/+7.7; W/L/T; CI; equal-$K$; E1/E12 appendix preview correct. |

---

## Chapter 2 — Background

| Sev | Finding |
|-----|---------|
| **Critical** | Trailing stray `)` after final sentence (line ~415) — **compile break**. |
| **Major** | Gap Summary restates C2/C3 claim tags that Ch.1 already owns — duplication vs brief “cut Gap vs Related.” Acceptable if short; still slightly FAQ-shaped. |
| Minor | Secondary vignette uses `classify_signal` while Ch.1 secondary is tax — allowed by brief, but cross-chapter secondary pair should stay labeled secondary everywhere. |
| OK | Concept-first order (SOFL → FSF → LLM → CEGIS → SMT → patterns → mutation → related) is Mentor-compliant. Related-work table is cohesive. |

---

## Chapter 3 — Formalization

| Sev | Finding |
|-----|---------|
| **Major** | Vignette witness **$(5,10)$** vs Method/Impl IR examples **$(3,10)$** — same residual story, inconsistent concrete model. Unify. |
| Minor | Roadmap figure is secondary-first (`classify_signal`); prose correctly flags primary catch-all — OK if captions stay explicit (they do). |
| Minor | “motivational” avoided here; Proposition for order-required is sound. |
| OK | Primary catch-all anchored; SpecIR/Accept/PDR/FAR definitions clean; no illegal FAR decimals. |

---

## Chapter 4 — Method

| Sev | Finding |
|-----|---------|
| **Major** | Empirical E2 PDR/FAR table in Method (preview of Results) — brief: Method may preview intent, not lead with result crowns. Soften prose so Results remain the home of the claim; keep bound illustration if needed. |
| Minor | Secondary trail figure still ordering-first after primary walkthrough — OK with captions. |
| Minor | Proposition labeled soundness (good); Remark “Scope relative to deployed suite” is fine. |
| OK | Primary catch-all end-to-end walkthrough is Mentor example-driven. FAR table uses **5.0% / 8.8%** correctly. No E6 win counts as mechanism crown. |

---

## Chapter 5 — Implementation

| Sev | Finding |
|-----|---------|
| Minor | Orchestration still cites historical `run_hard_full_parallel_v1` matrix sizes — risk of reader mixing corpora; label archive if kept. |
| Minor | JSON example uses $(3,10)$ — align with Ch.3 after unify. |
| OK | Primary vignette carried; Screen pluggability over taxonomy; no defensive reviewer FAQ. |

---

## Chapter 6 — Experimental Setup

| Sev | Finding |
|-----|---------|
| **Major** | Imperative “**Do not claim** M dominates all seeds” reads like reviewer instruction. State factually: “B2 leads every seed; M does not dominate all seeds.” |
| Minor | “stress-test” repeated as role for E1 — factual once is fine; three mentions edge toward slogan. |
| Minor | Still encyclopedia-length vs brief cut target; RQs + corpus card + mode table are necessary — further cut optional. |
| OK | Measurement correction disclosed once; corpora separated; authoritative run ids present. |

---

## Chapter 7 — Results

| Sev | Finding |
|-----|---------|
| **Critical** | Vignette break: intro/method use **3-scenario $S_3$ others**; E6 prose names **$S_8$ / scenario index~8** without bridging. Reader thinks the running example changed. Must say hard tasks use an 8-scenario skeleton with residual as last case (same *role* as intro $S_3$). |
| **Major** | “not uniqueness among structured traces / not a one-field necessity theorem” — defensive; rephrase as E14/field-ablation *finding*. |
| **Major** | “hygiene” subsection title and repeated “Conf. hygiene” — jargon cluster. |
| Minor | RQ3 opens on prevention after RQ1 — good Mentoring; secondary ordering mutants correctly marked. |
| OK | E2 table **95.0%/5.0% vs 91.2%/8.8%**; E6 stats; 14/14 others, 0/14 ordering; equal-$K$; E12 honesty. |

---

## Chapter 8 — Discussion

| Sev | Finding |
|-----|---------|
| **Major** | “**Motivational** FAR bound versus operational FAR” — brief forbids motivational-theorem presentation. Rename to finite-sample / theoretical envelope vs empirical E2. |
| Minor | Related-approaches section partly duplicates Ch.2 — cut opportunity. |
| Minor | “equal-$K$ hygiene” recurrence. |
| OK | Lead interpretation is acceptance safety; E6/E2/E12 numbers match card; limitations framed as limitations (not FAQ). |

---

## Chapter 8b — Industrial case

| Sev | Finding |
|-----|---------|
| **Critical** | Overlap/preemption (“link down” preempts “high latency”) is equated with “**the same … as the catch-all vignette**.” That is false: catch-all is residual output mismatch; this is **secondary ordering**. Mis-anchors the primary vignette. |
| **Major** | Closing “not a production CI claim” — defensive; prefer limitation wording. |
| OK | Deployment rule and saturation reading align with C4 / AUTHORITATIVE_NUMBERS. |

---

## Chapter 9 — Conclusion

| Sev | Finding |
|-----|---------|
| **Major** | Section **“Takeaways”** + label `sec:conc:remember` echoes forbidden “What a reviewer should remember.” Rename. |
| **Major** | “not an ordering-uniqueness proof” — defensive residue. |
| Minor | “hygiene” again in summary/closing. |
| OK | Numbers and deployment sentence match abstract/card; Accept lead is clear. |

---

## Cross-cutting Mentor scorecard

| Guideline | Grade | Note |
|-----------|-------|------|
| Abstract-then-Concrete | B− | Strong in abstract/Ch.3–4 walkthroughs; weak in Ch.1 contribution enumerate (caveats first). |
| Concept First | A− | Ch.2–3 order good; industrial case confuses concepts. |
| Example-Driven | B | Primary vignette present; S3↔S8 and (3,10)↔(5,10) break continuity. |
| Cohesive Integration | B+ | Tables/figures generally tied; Ch.2 stray `)` breaks build. |
| Voice (no defensiveness) | C+ | Main remaining Critical/Major cluster. |

---

## Fix priority (executed in staging `.tex`)

1. Remove Ch.2 stray `)`.  
2. Rewrite Ch.1 / Ch.7 / Ch.9 / industrial defensive Scope / “not a claim” / Takeaways.  
3. Bridge E6 $S_8$ to intro catch-all role; unify residual witness to $(3,10)$.  
4. Relabel industrial case as secondary ordering; soften Method/Discussion “motivational/hygiene” jargon where Critical/Major.  
5. Leave live `chapters/` and `hsp-agile-conference/` untouched.

---

## Post-fix status (2026-07-11)

Critical/Major language and vignette issues listed above were edited **in place** under `_rewrite/`. Live `chapters/` and `hsp-agile-conference/` were not touched.

**Remaining (Minor / optional):** Ch.2 Gap vs Related still slightly duplicative; Ch.5/6 length; related-work reprise in Ch.8; table captions outside staging that still say “not uniqueness” (`tables/*.tex`) — promote pass may need table caption polish separately.
