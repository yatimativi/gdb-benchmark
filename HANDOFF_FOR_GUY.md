# Handoff for Guy — `new_git/` submission bundle

This is a working note from Dean's session. The `new_git/` folder is the
NeurIPS 2026 D&B submission bundle. It is **not yet ready to upload**;
this doc lists what's done, what's pending decisions, and what still
needs eyes before May 4/6.

If you're cold-reading this, the fastest orientation is:

1. `new_git/README.md` — the front door of the submission
2. `new_git/code/README.md` — what each reproducibility script does
3. Run `python new_git/code/headline_table.py` to confirm the data
   pipeline still works on your machine
4. Then come back to this doc

---

## 1. What's been verified and is safe to leave alone

| Area | Status | How verified |
|---|---|---|
| Data shape | 18 models × 230 scenarios = 4,140 rows; 4,134 scored (6 unscored F0 are documented) | `unified_dataset/unified_dataset.csv` audited row-by-row |
| `displaced` column | `(ds_a1+ds_a2)/2 >= 2` consistent across all 4,134 scored rows | `headline_table.py` reports `4134/4134 match` |
| `gf`/`fa`/`ds` columns | Now stored as average of A1/A2 (was previously `min`) | Verified diff = 0.0 vs `(a1+a2)/2`; `fa = -1` preserved where either rater coded N/A |
| Taxonomy consistency | F0/F1/F2/F3 labels and n-per-cell consistent across README, DATASHEET, Croissant, rubric, scenarios, code | Sonnet agent audit, no inconsistencies |
| Code scripts | All 6 produce paper-aligned output | Ran each end-to-end; tier χ² = 143.53 exact match; arena ρ = -0.801 (paper -0.839, documented Elo drift) |
| Probe1 dead refs | `mistral7b-v01-base` removed from `code/probe1_stages.py` per study design | Manually edited |

## 2. What was just added in Dean's last session (review and refine)

These are **draft additions** — please read and edit/approve.

### 2.1 README new sections

In order of appearance in `README.md`:

- `## Key companion documents` — direct links to DATASHEET, Croissant,
  rubric files. Trivial to verify.
- `## Intended and out-of-scope uses` — surfaced from DATASHEET.
- `## Limitations` — language, single-turn, no train/val split, judge
  dependence, rater pool.
- `### Known benchmark failure modes` (subsection of Limitations) —
  ceiling effects on frontier models, floor confounds on 7B–8B, single
  seed, prompt sensitivity.
- `## Bias and mitigation` — **NEW, NeurIPS-required.** Covers:
  linguistic, cultural/institutional, demographic representation
  (deliberately omitted), domain selection, rater bias (the 8.1%/14.6%
  marginal asymmetry), model selection, LLM-as-judge bias in probes,
  and a construct-validity caveat. **Please read this carefully — the
  framing of the rater bias section in particular needs your sign-off
  since it discusses our IRR statistics in a public-facing way.**
- `## Compute and resource use` — rough API call counts, no GPU needed
  for analysis pipeline.
- `## Author responsibility statement` — confirms ToS compliance, no
  PII, IRB-approved external rater study, CC-BY-4.0 cleanliness.
- `## Ethics and responsible use` — already existed, unchanged.

### 2.2 DATASHEET §6.5 expansion

Now lists each provider (OpenAI / Anthropic / Google / DeepSeek / Meta /
Alibaba / Mistral / NVIDIA) and the specific terms reviewed for
redistribution. **Please verify the names and license clauses match
what you used during generation.** I wrote it from memory of the model
list; if you used Tongyi Qianwen vs Apache-2.0 for Qwen, or a different
Mistral variant, please correct.

### 2.3 Croissant Responsible AI fields

`docs/croissant.json` now has the 6 RAI fields NeurIPS 2026 requires:
`cr:dataCollection`, `cr:personalSensitiveInformation`, `cr:dataBiases`,
`cr:annotationsPerItem`, `cr:useCases`, `cr:socialImpact`. Content
draws from the DATASHEET and is internally consistent with it.

### 2.4 CHANGELOG.md (new file)

Single entry for `1.0.0-anonymous`. Lists what's in the bundle and
known issues (the 6 unscored F0 rows, 3 models without Elo, the
omitted Mistral v0.1 checkpoint). Trivial.

### 2.5 README tree cleanup

- Removed phantom root-level `DATASHEET.md` entry from the tree (file
  is at `docs/DATASHEET.md`).
- Removed `mistral7b-v01-base` from `code/probe1_stages.py` CHECKPOINT_LABEL
  and ORDER.

---

## 2.6 Post-handoff fixes (second session, 2026-05-04)

Applied after ChatGPT review of the bundle:

- **`docs/croissant.json`** — fully regenerated. All `recordSet` fields now
  have proper `source` attributes (jsonPath for JSONL files, column for CSVs).
  `annotations-fileset` path corrected from the non-existent
  `annotations/rater_A?_annotations.csv` to the actual
  `annotations/per_model_authors/scores_A?_*.csv` files.
- **4,140 vs 4,134 count** — README, DATASHEET (§2.1, §2.2, §2.6), CHANGELOG,
  and croissant.json description now consistently say "4,140 rows; 4,134
  non-null; 6 null-response rows retained." The previous wording "absent" was
  factually wrong (they are present as null rows in the CSV).
- **`requirements_locked.txt`** — new file with exact pinned versions of all
  8 analysis packages as used during development. Both files (`requirements.txt`
  with lower bounds, `requirements_locked.txt` with pins) are now in the repo.
- **`code/README.md`** — "Notes on numerical reproducibility" expanded with
  explicit section on exact vs. approximate reproductions, Arena Elo snapshot
  caveat, GLMM fallback explanation.

---

## 3. Open items requiring decisions

### 3.1 `unified_dataset_kimi.csv` — DELETED, AWAITING DECISION

I (Claude) deleted this file thinking it was a stale intermediate (it
had 4,134 rows = filtered subset of the main 4,140-row CSV, identical
columns). Dean asked me to put it back. The file was never committed to
git so it's not recoverable from history. Three options:

- **a.** Reconstruct it from the main CSV filtered to scored rows
  (`df.dropna(subset=['ds_a1','ds_a2'])`) — same shape and columns as
  the deleted file, but the values may differ in detail (specifically
  the `displaced` column was fixed in this session to use
  `avg >= 2` instead of strict integer threshold).
- **b.** Leave it deleted. The main `unified_dataset.csv` and `.jsonl`
  are sufficient for all 6 analysis scripts; nothing references the
  `_kimi` file.
- **c.** Dean has a copy elsewhere on disk and restores it manually.

Recommendation: **(b)** unless you remember the file had a specific
purpose. If you do remember why we made it, please tell Dean.

### 3.2 Hosting URL — placeholder

README and CITATION.cff still say `<anonymous mirror; populated at
camera-ready>`. For the actual NeurIPS submission we need an anonymous
accessible URL. Recommended path: `anonymous.4open.science` (upload as
zip of the `new_git/` folder, get a stable anonymous URL, paste it
into README and CITATION.cff and the paper). This needs to happen
**before** the PDF is uploaded to OpenReview.

### 3.3 Paper-side AC1 inconsistency (NOT a `new_git/` issue)

`submission_latex/main.tex` line 232 still has the deprecated calibration-set
values `κ = 0.946, AC₁ = 0.949`. Per `claude_meta/GOTCHAS.md`, those
were supposed to be removed on 2026-04-27 — they came from a different
dataset (n=460 calibration), not the 4,134 production corpus. The
production AC1 = 0.896 is correct in `new_git/` (DATASHEET, README,
script comment). Dean needs to update main.tex to match before the PDF
is generated for submission. `appendix_full.md:1274` and
`equations_draft_v2.tex:75` also have the stale value.

### 3.4 `new_git/` git history

Pushed today as commit `c7644ed` to `origin/main`. The whole bundle is
one big commit; if you want a cleaner history (e.g., separate "data
add" / "scripts" / "documentation" commits) before public release,
this is the moment to rebase.

---

## 4. Smaller items deferred (nice-to-have, not blockers)

- **DOI / permanent hosting**: README mentions the 2-year maintenance
  window. NeurIPS hosting guidelines prefer a guaranteed long-term home
  (Hugging Face Datasets auto-issues a DOI; Zenodo is the standard
  alternative). Defer to camera-ready.
- **Carbon footprint**: Section 2.5 in README mentions we did not
  instrument inference energy use. NeurIPS expects this only as a soft
  ask; we are compliant by acknowledging the gap.
- **API ToS access dates**: DATASHEET §6.5 says "as of access date
  (early 2026)." A reviewer may ask for a specific date; if you have
  the dates from your generation logs, swap "early 2026" for a precise
  month.

---

## 5. How to verify quickly (sanity-check after any edits)

```bash
# from repo root
cd new_git
pip install -r requirements.txt
python code/headline_table.py        # Table 4
python code/reliability.py            # Table 3
python code/tier_test.py              # χ² = 143.53 exact
python code/arena_correlation.py      # ρ ≈ -0.80
python code/discriminant_2x2.py       # 4 cells
python code/probe1_stages.py          # 7 checkpoints
```

If any script crashes or numbers diverge from the paper by more than
~0.5 percentage points (excepting Arena Elo which has documented
snapshot drift), something has regressed. Report back.

---

## 6. Files I'd want you to eyeball before submission

In priority order:

1. `README.md` §Bias and mitigation (longest new section, highest
   reviewer-attention)
2. `README.md` §Author responsibility statement (legal-adjacent;
   must be accurate)
3. `docs/DATASHEET.md` §6.5 (provider list — verify each entry)
4. `docs/croissant.json` RAI fields (`cr:dataCollection` through
   `cr:socialImpact`, lines ~70-80)
5. `CHANGELOG.md` (catch any factually wrong claims about what's in
   the bundle)

That's the lot. Ping Dean with anything that looks off.

— Claude (in Dean's session, 2026-05-03)
