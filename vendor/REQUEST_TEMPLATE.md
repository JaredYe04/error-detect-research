# Vendor / SpecTool data request template

Use this when contacting Hosei / ECNU collaborators or industrial partners.
Do **not** redistribute NDA artefacts into the public git tree; keep them under
`vendor/agile-sofl-toolchain/examples/` (gitignored if proprietary).

---

**To:** Shaoying Liu \<sliu@hosei.ac.jp\> (or local ECNU SOFL collaborator)  
**Subject:** Request for Agile-SOFL SpecTool `.asfl` examples for LLM repair evaluation

Dear Prof. Liu / colleagues,

We are evaluating specification-guided LLM repair (HSP-Agile / SgDP) on
ordered-guard FSF processes. Public GitHub does not host the historical
Agile-SOFL SpecTool example packs.

Could you share a **non-proprietary** subset of `.asfl` teaching / demo
specifications (ATM, hotel, banking, or simplified signalling processes)?
We only need process-level ordered scenarios (guards + postconditions); CDFD
graphics can be omitted.

We will:
- keep files under a local `vendor/` tree (not redistributed if restricted);
- cite provenance honestly (teaching pack vs industrial NDA);
- report aggregate Conf./PDR only, not proprietary process names if required.

Thank you,
[Name / affiliation / ORCID]

---

## Industrial NDA (Casco / Mitsubishi / Nippon Signal)

Ask for **process-level FSF only** (ordered scenarios), strip proprietary
graphics and site identifiers. Place under the same `examples/` folder and run:

```bash
python scripts/import_vendor_asfl.py --vendor-dir vendor/agile-sofl-toolchain/examples
```

Paper wording: **vendor-asfl pilot** only when `.asfl` import succeeds;
otherwise **published-industrial pilot** (`benchmarks/published_industrial_pilot.json`).
