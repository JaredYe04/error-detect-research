---
name: paper-english-polish-deai
description: >-
  Serial English LaTeX polish then de-AI rewrite for CS conference papers.
  Use when polishing HSP-Agile or other paper TeX, reducing AIGC tone,
  running expression-optimization then naturalness passes, or when the user
  asks for 表达润色 / 去AI味 on LaTeX prose.
disable-model-invocation: false
---

# Paper English: Polish then De-AI (Serial)

Apply **in order**. Never run de-AI before polish. Never review for acceptance in these two steps.

## Shared rules (both steps)

- Input/output is **English LaTeX only** (not PDF).
- Keep `\cite{}`, `\ref{}`, `\eg`, `\ie`, math `$...$`, and existing `\textbf{}`/`\emph{}`.
- Do **not** add new bold/italic for emphasis.
- Do **not** turn paragraphs into itemize/enumerate.
- Escape `%`, `_`, `&` in TeX text.
- Do **not** expand common abbreviations (keep `LLM` as `LLM`).
- Do **not** invent or change scientific numbers; align with `paper/hsp-agile/artifacts/AUTHORITATIVE_NUMBERS.md` when editing HSP-Agile.
- Prefer `of METHOD` / noun modifiers over `METHOD's`.
- No contractions (`it is`, `does not`).

Mentor readability (HSP-Agile): abstract claim first, then concrete detail; define terms; use examples; integrate figure, prose, and math.

## Step 1 — Expression polish

**Role:** Senior CS academic editor aiming at top-venue clarity (NeurIPS/ICLR/ICML bar).

**Goal:** Raise rigor, clarity, and readability to publication quality; fix every grammar/spelling/article/punctuation error. Prefer simple, clear research vocabulary over ornate wording.

**Output (exactly three parts, no extra chat):**

1. **Part 1 [LaTeX]** — polished English TeX only.
2. **Part 2 [Translation]** — Chinese direct translation; do **not** put English in parentheses after Chinese terms.
3. **Part 3 [Modification Log]** — brief Chinese notes on what changed (syntax, tone, errors fixed).

## Step 2 — De-AI / naturalness

**Role:** Senior CS academic editor reducing machine-generated tone toward native researcher prose (ACL/NeurIPS bar).

**Goal:** Replace mechanical phrasing with plain, precise academic English.

**Do:**

- Prefer plain verbs (`use`, `investigate`) over overused flourish (`leverage`, `delve into`, `tapestry`) unless truly technical.
- Drop stiff connectors (`First and foremost`, `It is worth noting that`); connect by logic.
- Prefer commas, parentheses, or clauses over em-dashes.

**Critical threshold:** If the text is already natural, **keep it**. Do not edit for the sake of editing.

**Output (exactly three parts, no extra chat):**

1. **Part 1 [LaTeX]** — rewritten TeX, or the original if unchanged.
2. **Part 2 [Translation]** — Chinese direct translation.
3. **Part 3 [Modification Log]** — what mechanical phrases were removed; **or** exactly:  
   `[检测通过] 原文表达地道自然，无明显 AI 味，建议保留。`

**Self-check before finishing Step 2:** Does the change actually improve readability? If it is only synonym-swapping, revert and mark 检测通过.

## Pipeline for full papers

1. Polish full TeX body → staging file.
2. De-AI **only** the polished staging file → natural staging file.
3. Apply natural file to the manuscript; compile; then (optional) reviewer pass as a **separate** step.

## HSP-Agile paths

- Conference: `paper/hsp-agile-conference/main.tex`
- Full report: `paper/hsp-agile/front/abstract.tex`, `paper/hsp-agile/chapters/*.tex`
- Numbers: `paper/hsp-agile/artifacts/AUTHORITATIVE_NUMBERS.md`

## Additional resources

- Prompt templates (Chinese source constraints): [prompt-templates.md](prompt-templates.md)
