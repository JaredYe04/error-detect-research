# Bibliography Verification Report

**File verified:** `paper/hsp-agile/bib/references.bib`  
**Date:** 2026-07-10  
**Method:** For each `@` entry, web search (Google Scholar–indexed sources, publisher pages, DOI resolvers, arXiv, IEEE Xplore, ACM DL, NIST, Springer) for title + first author; DOI/arXiv ID cross-check where present.  
**Entries in file:** 40 (user cited 39; one duplicate pair: `loughman2024dafnybench` / `dafnybench2024`).

---

## Per-entry results

### liu1997sofl
- **Claimed:** Liu, Shaoying. *SOFL: A Formal Engineering Methodology for Industrial Applications*. IEEE Computer Society Press book, 1997.
- **Found:** Same title exists as **IEEE Transactions on Software Engineering** 24(1):24–45, **January 1998** (DOI [10.1109/32.663996](https://doi.org/10.1109/32.663996)); co-authors include A. Jefferson Offutt, Chris Ho-Stuart, Yong Sun, Mitsuru Ohba. Earlier 1997 RE conference abstract also exists.
- **Status:** MISMATCH
- **Notes:** Not a 1997 book; mis-typed as `@book`. Should be `@article` (TSE 1998) or `@inproceedings` (RE 1997).

### liu2004sofl
- **Claimed:** Liu, Shaoying. "A Practical Formal Method Based on SOFL for Software Development." *Formal Aspects of Computing* 16(1):44–66, 2004. DOI 10.1007/s00165-003-0022-9.
- **Found:** No matching Liu/SOFL article in FAC vol. 16 on Google Scholar or publisher indexes. DOI **10.1007/s00165-003-0022-9 returns HTTP 404**; web search indicates this DOI is not Liu’s SOFL paper. Liu’s related 2004 work is the **book** *Formal Engineering for Industrial Software Development* (Springer).
- **Status:** NOT FOUND
- **Notes:** Title/venue/DOI combination appears **fabricated or conflated** with another FAC article. Treat as hallucinated until a real citation is supplied.

### liu2014sofl
- **Claimed:** Liu, Shaoying. *Formal Engineering for Industrial Software Development: Using the SOFL Method*. Springer, **2014**. DOI 10.1007/978-3-642-54233-7.
- **Found:** Same book, Springer, **March 2004** (ISBN 978-3-540-20602-6); DOI [10.1007/978-3-662-07287-5](https://doi.org/10.1007/978-3-662-07287-5). Paperback reprint ~2010.
- **Status:** MISMATCH
- **Notes:** Wrong year and wrong DOI; title and author are correct.

### li2022agilesofl
- **Claimed:** Li, Xiaohong & Liu, Shaoying. "Fault Prevention in Agile-SOFL: A Test-Driven Conformance Approach." QRS 2022, pp. 312–322. DOI 10.1109/QRS57517.2022.00041.
- **Found:** DOI [10.1109/QRS57517.2022.00041](https://doi.org/10.1109/QRS57517.2022.00041) resolves to **"A New Code Review Method based on Human Errors"** by **Fuqun Huang, Bo Zhao, Henrique Madeira**, QRS 2022, pp. **321–332**. No Google Scholar hit for the claimed title/authors. Liu group’s real Agile-SOFL QRS work is by **Jiandong Li** (not Xiaohong Li), companion proceedings, different titles/DOIs.
- **Status:** NOT FOUND
- **Notes:** **Critical hallucination** — claimed metadata does not exist; attached DOI belongs to an unrelated paper.

### li2023iet
- **Claimed:** Li, Xiaohong & Liu, Shaoying. "An Automated Fault-Detection Framework for Agile-SOFL Formal Specifications Using Mutation-Based Oracles." *IET Software* 17(4):389–403, 2023. DOI 10.1049/sfw2.12091.
- **Found:** DOI [10.1049/sfw2.12091](https://doi.org/10.1049/sfw2.12091) is **"Scientific programming using optimized machine learning techniques for software fault prediction…"** by **Muhammad Shafiq et al.**, *IET Software* 2023 — **RETRACTED**. No trace of the claimed Agile-SOFL/mutation-oracle title. Related real paper: **Jiandong Li & Shaoying Liu**, "Requirements-related fault prevention during the transformation from formal specifications to programs," *IET Software* 17(3):316–332, 2023, DOI [10.1049/sfw2.12126](https://doi.org/10.1049/sfw2.12126).
- **Status:** NOT FOUND
- **Notes:** **Critical hallucination** — wrong authors, title, volume/pages; DOI points to unrelated retracted article.

### chen2021codex
- **Claimed:** Chen, Mark et al. "Evaluating Large Language Models Trained on Code." arXiv:2107.03374, 2021.
- **Found:** [arXiv:2107.03374](https://arxiv.org/abs/2107.03374) — Codex / HumanEval paper, OpenAI, July 2021.
- **Status:** ARXIV-ONLY (VERIFIED)
- **Notes:** Preprint only in bib; widely cited.

### dakhel2023copilot
- **Claimed:** Dakhel, Arghavan Moradi et al. "GitHub Copilot AI Pair Programmer: Asset or Liability?" *J. Systems and Software* 203:111734, 2023.
- **Found:** [DOI 10.1016/j.jss.2023.111734](https://doi.org/10.1016/j.jss.2023.111734) — title, authors, venue, year match.
- **Status:** VERIFIED

### li2022alphacode
- **Claimed:** Li, Yujia et al. "Competition-Level Code Generation with AlphaCode." *Science* 378(6624):1092–1097, 2022.
- **Found:** [DOI 10.1126/science.abq1158](https://doi.org/10.1126/science.abq1158) — DeepMind AlphaCode, *Science* Dec 2022.
- **Status:** VERIFIED

### openai2023gpt4
- **Claimed:** OpenAI. *GPT-4 Technical Report*, 2023. arXiv:2303.08774.
- **Found:** [arXiv:2303.08774](https://arxiv.org/abs/2303.08774) exists; OpenAI technical report.
- **Status:** ARXIV-ONLY (VERIFIED)

### lynn2024verifierloop
- **Claimed:** Lynn, Tomas et al. "Verifier-in-the-Loop LLM Code Synthesis: Closing the Formal Specification Gap." *ACM TOSEM* 33(5), 2024. DOI 10.1145/3640340.
- **Found:** No Google Scholar / ACM hit for Lynn, Sheridan, Guerin & Duan with this title. DOI [10.1145/3640340](https://doi.org/10.1145/3640340) resolves to **"Human Emotion Recognition Based on Machine Learning Algorithms with Low Resource Environment"** by **P. Asha et al.**, *ACM Trans. Asian Low-Resource Lang. Inf. Process.*, 2024. Related real verifier+LLM work includes **Clover** (Sun, Sheng, Padon, Barrett; arXiv:2310.17807; SAIV 2024 proceedings).
- **Status:** NOT FOUND
- **Notes:** **Critical hallucination** — paper and authors appear invented; DOI is unrelated.

### loughman2024dafnybench
- **Claimed:** Loughman, Jacob & Ringer, Talia. "DafnyBench: A Benchmark for Formal Software Verification." arXiv:2406.08467, 2024.
- **Found:** [arXiv:2406.08467](https://arxiv.org/abs/2406.08467) — title and authors match.
- **Status:** ARXIV-ONLY (VERIFIED)

### yang2024qwen25
- **Claimed:** Yang, An et al. "Qwen2.5 Technical Report." arXiv:2412.15115, 2024.
- **Found:** [arXiv:2412.15115](https://arxiv.org/abs/2412.15115) exists.
- **Status:** ARXIV-ONLY (VERIFIED)

### demoura2008z3
- **Claimed:** de Moura, Leonardo & Bjørner, Nikolaj. "Z3: An Efficient SMT Solver." TACAS 2008, LNCS 4963, pp. 337–340.
- **Found:** [DOI 10.1007/978-3-540-78800-3_24](https://doi.org/10.1007/978-3-540-78800-3_24) — matches.
- **Status:** VERIFIED

### solarlezama2008sketching
- **Claimed:** Solar-Lezama, Armando. "Program Synthesis by Sketching." PhD thesis, UC Berkeley, 2008.
- **Found:** [EECS-2008-176](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2008/EECS-2008-176.html) / thesis PDF — Fall 2008.
- **Status:** VERIFIED

### leino2010dafny
- **Claimed:** Leino, K. Rustan M. "Dafny: An Automatic Program Verifier for Functional Correctness." LPAR 2010, LNCS 6355, pp. 348–370.
- **Found:** [DOI 10.1007/978-3-642-17511-4_20](https://doi.org/10.1007/978-3-642-17511-4_20) — matches.
- **Status:** VERIFIED

### harman2012formalagile
- **Claimed:** Harman, Mark & Clark, John. "Metrics Are Fitness Functions Too." Listed as `@article` in *10th IEEE International Software Metrics Symposium*, pp. 58–69, year **2004** (key says 2012).
- **Found:** [DOI 10.1109/metrics.2004.30](https://doi.org/10.1109/metrics.2004.30) — **10th IEEE Metrics Symposium, 2004**, pp. 58–69. Title and authors correct.
- **Status:** MISMATCH
- **Notes:** Wrong entry type (`@inproceedings`); wrong `journal` field; misleading cite key `harman2012formalagile`. Paper is search-based SE, not formal/agile methods per se.

### hovemeyer2004findbugs
- **Claimed:** Hovemeyer, David & Pugh, William. "Finding Bugs Is Easy." OOPSLA Companion, pp. 92–106, 2004.
- **Found:** [DOI 10.1145/1052883.1052895](https://doi.org/10.1145/1052883.1052895) — *ACM SIGPLAN Notices* 39(12):92–106, 2004.
- **Status:** VERIFIED

### ayewah2008findbugs
- **Claimed:** Ayewah, Nathaniel et al. "Evaluating Static Analysis Defect Warnings on Production Software." *ACM SIGPLAN Workshop PASTE*, pp. 1–8, **2007** (key says 2008).
- **Found:** [DOI 10.1145/1251535.1251536](https://doi.org/10.1145/1251535.1251536) — PASTE **2007**; title and authors match.
- **Status:** MISMATCH
- **Notes:** Should be `@inproceedings`; cite key year wrong (2008 vs 2007).

### demillo1978mutation
- **Claimed:** DeMillo, Richard A. et al. "Hints on Test Data Selection…" *Computer* 11(4):34–41, 1978.
- **Found:** [DOI 10.1109/C-M.1978.218136](https://doi.org/10.1109/C-M.1978.218136) — classic mutation testing paper.
- **Status:** VERIFIED

### offutt1992mutation
- **Claimed:** Offutt, A. Jefferson & Untch, Roland H. "Mutation Testing Enters the Twenty-First Century." *Mutation 2000…*, pp. 34–44, **2001** (key says 1992).
- **Found:** Actual title: **"Mutation 2000: Uniting the Orthogonal"** — MUTATION'00 workshop / Kluwer book chapter, **2001**, pp. 34–44 ([DOI 10.1007/978-1-4757-5939-6_7](https://doi.org/10.1007/978-1-4757-5939-6_7)).
- **Status:** MISMATCH
- **Notes:** **Wrong title** (likely hallucinated subtitle). Year in bib (2001) is correct; key is wrong.

### okun2007mutation
- **Claimed:** Okun, Vadim et al. "Report on the Static Analysis Tool Exposition (SATE) IV." NIST SP 500-297, **2007**.
- **Found:** [NIST SP 500-297](https://doi.org/10.6028/NIST.SP.500-297) — **January 2013**; authors Okun, Delaitre, Black. Title matches; topic is **static analysis**, not mutation testing.
- **Status:** MISMATCH
- **Notes:** Wrong year; miscategorized under mutation; should be `@techreport` with year 2013.

### zhu1997specification
- **Claimed:** Zhu, Hong et al. "Software Unit Test Coverage and Adequacy." *ACM Computing Surveys* 29(4):366–427, 1997.
- **Found:** [DOI 10.1145/267580.267590](https://doi.org/10.1145/267580.267590) — matches.
- **Status:** VERIFIED

### claessen2000quickcheck
- **Claimed:** Claessen, Koen & Hughes, John. "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs." ICFP 2000, pp. 268–279.
- **Found:** [DOI 10.1145/351240.351266](https://doi.org/10.1145/351240.351266) — matches.
- **Status:** VERIFIED

### ammann2016testing
- **Claimed:** Ammann, Paul & Offutt, Jeff. *Introduction to Software Testing*, 2nd ed., Cambridge University Press, 2016.
- **Found:** ISBN 978-1-107-17201-2; [DOI 10.1017/9781316771273](https://doi.org/10.1017/9781316771273); published Dec 2016.
- **Status:** VERIFIED

### beck2001xp
- **Claimed:** Beck, Kent. *Extreme Programming Explained: Embrace Change*, 2nd ed., Addison-Wesley, **2004** (key says 2001).
- **Found:** 2nd edition, Nov 2004, ISBN 0321278658 (with Cynthia Andres).
- **Status:** VERIFIED
- **Notes:** Bib `year={2004}` is correct; cite key `beck2001xp` is misleading.

### pohl2010requirements
- **Claimed:** Pohl, Klaus. *Requirements Engineering: Fundamentals, Principles, and Techniques.* Springer, 2010.
- **Found:** [DOI 10.1007/978-3-642-12578-2](https://doi.org/10.1007/978-3-642-12578-2) — Springer 2010.
- **Status:** VERIFIED

### barrett2018smt
- **Claimed:** Barrett, Clark & Tinelli, Cesare. "Satisfiability Modulo Theories." *Handbook of Model Checking*, pp. 305–343, 2018.
- **Found:** [DOI 10.1007/978-3-319-10575-8_11](https://doi.org/10.1007/978-3-319-10575-8_11) — matches.
- **Status:** VERIFIED

### woodcock2009formalsurvey
- **Claimed:** Woodcock, Jim et al. "Formal Methods: Practice and Experience." *ACM Computing Surveys* 41(4), 2009.
- **Found:** [DOI 10.1145/1592434.1592436](https://doi.org/10.1145/1592434.1592436) — matches.
- **Status:** VERIFIED

### back1998refinement
- **Claimed:** Back, Ralph-Johan & von Wright, Joakim. *Refinement Calculus: A Systematic Introduction.* Springer, 1998.
- **Found:** [DOI 10.1007/978-1-4612-1674-2](https://doi.org/10.1007/978-1-4612-1674-2) — matches.
- **Status:** VERIFIED

### cousot1977abstract
- **Claimed:** Cousot, Patrick & Cousot, Radhia. "Abstract Interpretation…" POPL 1977, pp. 238–252.
- **Found:** [DOI 10.1145/512950.512973](https://doi.org/10.1145/512950.512973) — matches.
- **Status:** VERIFIED

### dijkstra1975guarded
- **Claimed:** Dijkstra, Edsger W. "Guarded Commands, Nondeterminacy and Formal Derivation of Programs." *CACM* 18(8):453–457, 1975.
- **Found:** [DOI 10.1145/360933.360975](https://doi.org/10.1145/360933.360975) — matches.
- **Status:** VERIFIED

### wang2024opendevin
- **Claimed:** Wang, Xingyao et al. "OpenDevin: An Open Platform for AI Software Developers as Generalist Agents." arXiv:2407.16741, 2024.
- **Found:** [arXiv:2407.16741](https://arxiv.org/abs/2407.16741) — project now known as **OpenHands**; title/authors/year match preprint.
- **Status:** ARXIV-ONLY (VERIFIED)

### yang2024sweagent
- **Claimed:** Yang, John et al. "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering." arXiv:2405.15793, 2024.
- **Found:** [arXiv:2405.15793](https://arxiv.org/abs/2405.15793); NeurIPS 2024.
- **Status:** ARXIV-ONLY (VERIFIED)

### li2022qrs
- **Claimed:** Li, Xiaohong & Liu, Shaoying. "Early Fault Prevention in Formal Agile Development." QRS 2022, pp. 301–311.
- **Found:** **No** Google Scholar / IEEE / QRS 2022 proceedings hit for this exact title or author pair. QRS 2022 TOC around pp. 299–311 lists unrelated papers (e.g., LogGD p.299; Hezhen Liu ontology paper p.311). Liu’s verified QRS 2022 work uses **Jiandong Li**, different titles, companion track pp. 359–367.
- **Status:** NOT FOUND
- **Notes:** **Likely hallucinated** — no bibliographic record found.

### dafnybench2024
- **Claimed:** Duplicate of `loughman2024dafnybench` (same title, authors, arXiv ID).
- **Found:** arXiv:2406.08467 verified (see above).
- **Status:** ARXIV-ONLY (VERIFIED)
- **Notes:** Redundant key; consolidate to one entry.

### madaan2023selfrefine
- **Claimed:** Madaan, Aman et al. "Self-Refine: Iterative Refinement with Self-Feedback." NeurIPS 2023.
- **Found:** NeurIPS 2023 proceedings ([paper PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/91edff07232fb1b55a505a9e9f6c0ff3-Paper-Conference.pdf)); arXiv:2303.17651.
- **Status:** VERIFIED

### chen2023selfdebug
- **Claimed:** Chen, Xinyun et al. "Teaching Large Language Models to Self-Debug." ICLR 2024.
- **Found:** ICLR 2024; arXiv [2304.05128](https://arxiv.org/abs/2304.05128).
- **Status:** VERIFIED

### shinn2023reflexion
- **Claimed:** Shinn, Noah et al. "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023.
- **Found:** NeurIPS 2023 ([proceedings PDF](https://proceedings.neurips.cc/paper_files/paper/2023/file/1b44b878bb782e6954cd888628510e90-Paper-Conference.pdf)).
- **Status:** VERIFIED

### chen2022codet
- **Claimed:** Chen, Bei et al. "CodeT: Code Generation with Generated Tests." ICLR 2023 (key says 2022).
- **Found:** ICLR 2023 poster; arXiv:2207.10397 (July 2022 preprint).
- **Status:** VERIFIED
- **Notes:** Bib `year={2023}` matches conference; key `chen2022codet` reflects arXiv year.

### austin2021mbpp
- **Claimed:** Austin, Jacob et al. "Program Synthesis with Large Language Models." arXiv:2108.07732, 2021 (MBPP).
- **Found:** [arXiv:2108.07732](https://arxiv.org/abs/2108.07732) — Google MBPP dataset paper.
- **Status:** ARXIV-ONLY (VERIFIED)

---

## Summary

| Category | Count |
|----------|------:|
| **VERIFIED** (peer-reviewed / books / proceedings) | 21 |
| **ARXIV-ONLY** (ID exists; no journal version in bib) | 8 |
| **MISMATCH** (real work, wrong metadata) | 6 |
| **NOT FOUND** (no matching publication) | 5 |
| **Total `@` entries** | 40 |

### Keys needing fix (priority order)

| Priority | Key | Issue |
|----------|-----|-------|
| **P0 – remove/replace** | `lynn2024verifierloop` | Invented paper; DOI is another article entirely |
| **P0 – remove/replace** | `li2023iet` | Invented paper; DOI is retracted unrelated article |
| **P0 – remove/replace** | `li2022agilesofl` | Invented paper; DOI is Huang et al. code-review paper |
| **P0 – remove/replace** | `li2022qrs` | No bibliographic record found |
| **P0 – remove/replace** | `liu2004sofl` | No matching publication; DOI dead/wrong |
| **P1 – correct metadata** | `liu1997sofl` | TSE 1998 article, not 1997 book |
| **P1 – correct metadata** | `liu2014sofl` | Book year 2004, DOI 10.1007/978-3-662-07287-5 |
| **P2 – correct metadata** | `harman2012formalagile` | `@inproceedings`, Metrics 2004 |
| **P2 – correct metadata** | `offutt1992mutation` | Title "Mutation 2000: Uniting the Orthogonal" |
| **P2 – correct metadata** | `okun2007mutation` | NIST SP 500-297, **2013**; not mutation |
| **P2 – correct metadata** | `ayewah2008findbugs` | PASTE **2007** |
| **P3 – cleanup** | `dafnybench2024` | Duplicate of `loughman2024dafnybench` |
| **P3 – cleanup** | `beck2001xp`, `chen2022codet`, keys | Keys disagree with years (optional rename) |

### Critical hallucinations

Five entries appear to be **fabricated or severely mis-attributed** with no supporting Google Scholar record:

1. **`lynn2024verifierloop`** — Authors/title/venue invented; DOI `10.1145/3640340` = emotion-recognition paper (Asha et al., TALLIP 2024).
2. **`li2023iet`** — Title/authors invented; DOI `10.1049/sfw2.12091` = retracted Shafiq et al. ML fault-prediction paper.
3. **`li2022agilesofl`** — Title/authors/pages invented; DOI `10.1109/QRS57517.2022.00041` = Huang et al. code-review paper.
4. **`li2022qrs`** — "Early Fault Prevention in Formal Agile Development" by Li Xiaohong & Liu not found in QRS 2022.
5. **`liu2004sofl`** — FAC article + DOI combination not found (DOI 404).

The Agile-SOFL corpus should instead cite verified works by **Jiandong Li & Shaoying Liu** (e.g., IET Software 2023, DOI 10.1049/sfw2.12126; QRS-C 2022, DOI 10.1109/QRS-C57518.2022.00060).

---

## Appendix: Proposed corrected BibTeX (MISMATCH / NOT FOUND entries)

```bibtex
@article{liu1998sofl,
  author  = {Liu, Shaoying and Offutt, A. Jefferson and Ho-Stuart, Chris and Sun, Yong and Ohba, Mitsuru},
  title   = {{SOFL}: A Formal Engineering Methodology for Industrial Applications},
  journal = {IEEE Transactions on Software Engineering},
  volume  = {24},
  number  = {1},
  pages   = {24--45},
  year    = {1998},
  doi     = {10.1109/32.663996}
}

@book{liu2004soflbook,
  author    = {Liu, Shaoying},
  title     = {Formal Engineering for Industrial Software Development: Using the {SOFL} Method},
  publisher = {Springer},
  year      = {2004},
  address   = {Berlin, Heidelberg},
  doi       = {10.1007/978-3-662-07287-5}
}

@article{li2023iet_faultprevention,
  author  = {Li, Jiandong and Liu, Shaoying},
  title   = {Requirements-Related Fault Prevention during the Transformation from Formal Specifications to Programs},
  journal = {{IET} Software},
  volume  = {17},
  number  = {3},
  pages   = {316--332},
  year    = {2023},
  doi     = {10.1049/sfw2.12126}
}

@inproceedings{li2022qrs_companion,
  author    = {Li, Jiandong and Liu, Shaoying},
  title     = {Requirements-Related Fault Prevention Mechanism for {SOFL} Formal Specification-Based Programming},
  booktitle = {Proc.\ 22nd {IEEE} Int.\ Conf.\ Software Quality, Reliability and Security Companion ({QRS-C})},
  pages     = {359--367},
  year      = {2022},
  publisher = {{IEEE}},
  doi       = {10.1109/QRS-C57518.2022.00060}
}

@inproceedings{harman2004maff,
  author    = {Harman, Mark and Clark, John A.},
  title     = {Metrics Are Fitness Functions Too},
  booktitle = {Proc.\ 10th {IEEE} Int.\ Symp.\ Software Metrics},
  pages     = {58--69},
  year      = {2004},
  doi       = {10.1109/metrics.2004.30}
}

@incollection{offutt2001mutation2000,
  author    = {Offutt, A. Jefferson and Untch, Roland H.},
  title     = {Mutation 2000: Uniting the Orthogonal},
  booktitle = {Mutation Testing for the New Century},
  pages     = {34--44},
  year      = {2001},
  publisher = {Kluwer},
  doi       = {10.1007/978-1-4757-5939-6_7}
}

@techreport{okun2013sate4,
  author      = {Okun, Vadim and Delaitre, Aur{\'e}lien and Black, Paul E.},
  title       = {Report on the Static Analysis Tool Exposition ({SATE}) {IV}},
  institution = {{NIST}},
  number      = {NIST SP 500-297},
  year        = {2013},
  doi         = {10.6028/NIST.SP.500-297}
}

@inproceedings{ayewah2007findbugs,
  author    = {Ayewah, Nathaniel and Pugh, William and Morgenthaler, J. David and Penix, John and Zhou, YuQian},
  title     = {Evaluating Static Analysis Defect Warnings on Production Software},
  booktitle = {Proc.\ {ACM SIGPLAN}-{SIGSOFT} Workshop on Program Analysis for Software Tools and Engineering ({PASTE})},
  pages     = {1--8},
  year      = {2007},
  doi       = {10.1145/1251535.1251536}
}
```

**Replace `lynn2024verifierloop`** with a verified alternative if a verifier-in-the-loop citation is needed, e.g.:

```bibtex
@inproceedings{sun2024clover,
  author    = {Sun, Chuyue and Sheng, Ying and Padon, Oded and Barrett, Clark},
  title     = {Clover: Closed-Loop Verifiable Code Generation},
  booktitle = {Proc.\ 1st Int.\ Symp.\ {AI} Verification ({SAIV} 2024)},
  series    = {Lecture Notes in Computer Science},
  year      = {2024},
  eprint    = {2310.17807},
  archivePrefix = {arXiv}
}
```

**Remove without replacement:** `liu2004sofl` (FAC article), `li2022agilesofl`, `li2022qrs` unless primary sources are obtained from authors.

---

*Report generated by automated web verification; DOI resolver results checked 2026-07-10.*
