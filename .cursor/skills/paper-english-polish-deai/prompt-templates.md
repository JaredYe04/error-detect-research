# Source prompt templates (synonymously adapted for agents)

Use these as the operational checklist. Prefer the SKILL.md workflow for day-to-day runs.

## Expression polish checklist

- Top-venue formal tone; fix all surface errors.
- Simple & Clear vocabulary; no fancy padding.
- No contractions; avoid METHOD+'s possessives.
- Keep domain abbreviations and LaTeX commands.
- Keep existing emphasis; never add new emphasis.
- Keep paragraph form (no listification).
- Emit Part1 LaTeX / Part2 Chinese translation / Part3 Chinese log only.

## De-AI checklist

- Plain precise words; ban leverage/delve/tapestry-style filler unless needed.
- No listification; drop First and foremost / It is worth noting that.
- Fewer em-dashes.
- No new bold/italic in body.
- Edit only when needed; otherwise `[检测通过] 原文表达地道自然，无明显 AI 味，建议保留。`
- Emit Part1 / Part2 / Part3 only.

## Serial order

Polish → De-AI → (optional) Reviewer. Parallelizing polish with de-AI on the same draft is incorrect.
