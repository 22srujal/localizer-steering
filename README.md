# localizer-steering

Can planted text in a repository (comments, docstrings, instruction-style notes, bait functions) steer the
localization stage of an LLM coding agent toward a decoy function? The study uses 40 tasks (17 FastAPI, 15 Rich,
8 Requests) with Gemma 4 31B (QAT w4a16) on Kaggle at temperature 0. All reported results use 39 of the 40 tasks,
after dropping rich_3934 (see the caveats). Three localizers are compared.

- **A1** sees a repo map with names only.
- **A1.5** sees a repo map with names and signatures.
- **A2** sees the repo map, then reads up to 3 modules.

Four trap types (T1 maintainer comment, T2 docstring claim, T3 instruction-style note, T4 bait function) are planted
either in the decoy itself or as a pointer inside a gold module that points at the decoy.

## Headline results (39 tasks)

One definition is used everywhere. A decoy is named when it is in the answer's top 5 functions, and newly steered when
it is named on the trap run and not on the clean run of the same session. Clean is 0 for every variant, so newly steered
equals the trap count.

| Variant | A1 | A1.5 | A2 |
|---|---|---|---|
| T4 bait function | 13 | 9 | 11 |
| T3 pointer | 0 | 0 | 7 |
| T1 pointer | 0 | 0 | 3 |
| T3 in decoy | 0 | 0 | 2 |
| T1 in decoy | 0 | 0 | 1 |
| T2 pointer and T2 in decoy | 0 | 0 | 0 |

Over 21 tests, Bonferroni and Holm keep only T4 on A1 and A2. Benjamini-Hochberg adds T4 on A1.5. The T3 pointer on A2
(7 of 39, p=0.0156) survives none of them. A2 read the planted pointer in 28 of 39 tasks. It followed the T3 pointer in 7
of those 28 and in 0 of the 11 where it did not read the note. Full tables are in `Analysis_final_v2/tables.md`.

## Canonical folders

| Folder | Role | Canonical |
|---|---|---|
| `Phase_3/` | Trap runs from the pilot session (T1 decoy, T3 pointer, T4) plus that session's clean runs | Yes (traps) |
| `Phase_3_v2/` | Trap runs from the rest session (T1 pointer, T2 decoy, T2 pointer, T3 decoy) plus that session's clean runs | Yes (traps) |
| `Phase_2_v2/` | Clean localizer runs with the fixed localizer | Yes (Phase 2 clean table) |
| `Phase_2/` | First clean runs. `loc_A2.json` comes from the old, buggy A2 | Historical |
| `Analysis_final_v2/` | Final tables, CSV and figure on 39 tasks with one definition of decoy named | Yes (analysis) |
| `Analysis_final/` | First analysis pass on 40 tasks with a mixed module and function metric | Superseded, kept as the audit trail |
| repo root | BM25 baselines, the fixed `localizer.py`, the reanalysis notebook, handover and plan documents | Mixed |

Frozen files, do not edit. Every result and spec file in `Phase_3*/`, `Phase_2*/loc_*.json`, `bm25_results.json`,
`task_set_40.json`, both `trap_gen.py` files, and the `localizer.py` copy inside each Phase folder. Those copies record
exactly what ran and still carry the old module parser.

## What each file is

| File | Contents |
|---|---|
| `task_set_40.json` (identical copies in `Phase_2_v2/`, `Phase_3/`, `Phase_3_v2/`) | The 40 tasks with gold functions and gold files |
| `Phase_3*/clean_{A1,A1.5,A2}.json` | Clean run for that session, one row per task with answer modules and functions, gold ranks and A2 shown nodes |
| `Phase_3*/trap_{variant}_{loc}.json` | The same rows under a trap, plus `decoy_fn_rank`, `decoy_mod_rank` and for A2 `trap_seen` (A2 was shown the planted text) |
| `Phase_3*/spec_{variant}.json` | Decoy or bait id per task, host node of the planted text, and `meta` (hops, placement) |
| `Phase_3*/summary_p3.txt` | Printed summary from `trap_gen.analyze`, which uses the looser module-or-function metric. Do not cite it |
| `Phase_2*/loc_*.json`, `summary*.txt` | Clean Phase 2 runs. `loc_A2_v2.json` is the fixed A2 rerun and `loc_A1_rerun.json` is the A1 noise rerun |
| `Phase_2/localizer_v1_buggy.py` | Old localizer restored from commit `a7c2c22`. It produced `Phase_2/loc_A2.json` |
| `localizer.py` (root) | Localizers with the fixed module parser (a component starting with underscores then a capital letter is a class) |
| `bm25_results.json` | BM25 baselines B1 and B2, clean only, made by `bm25_base.py` |
| `Phase3_Reanalysis_v2.ipynb` | Reads the saved results and writes every table and the figure on 39 tasks |
| `Analysis_final_v2/tables.md` | Decoy named, multiple-testing correction, exposure split, pointer wording comparison, gold loss and drift, clean accuracy |
| `Analysis_final_v2/all_results.csv` | One row per variant and localizer with every metric |
| `Analysis_final_v2/figure_a2_decoy_named.png` | Newly steered share for the comment variants on A2 and for T4 on all localizers, with Wilson intervals |
| `Analysis_final/` | First analysis pass on 40 tasks, including `NOTES.md` on numbers that could not be reproduced |

## Rerunning the analysis (no GPU)

```bash
pip install matplotlib
jupyter notebook Phase3_Reanalysis_v2.ipynb
```

Run all cells from the repo root, next to `Phase_3/` and `Phase_3_v2/`. The notebook reads only saved JSON files. It
checks every p-value against an independent exact binomial test and writes its outputs to `Analysis_final_v2/`. Set
`REPO` in the first code cell if it cannot find the folders.

Rerunning the experiments themselves needs Kaggle, with the competition data, the wheelhouse and the model. The notebooks
`Phase_3*/Phase3_Traps.ipynb` write their own code into `/kaggle/working`. A full Phase 3 rerun takes about 3.5 GPU-hours
on L4 x4 and will not reproduce byte for byte, because temperature 0 is not deterministic here.

## Known caveats

1. **rich_3934 is dropped.** Its decoy `rich.live._RefreshThread.run` sits inside the gold file `rich/live.py`. The old
   `module_of_node` read `_RefreshThread` as a module, so the different-module check let it through. The parser is fixed
   in the root `localizer.py`, and no other task has a decoy or bait inside a gold file. The frozen runs used the old
   parser, so the fix matters only for a rerun. On all 40 tasks the T3 pointer on A2 was 8 steered (p=0.0078) and survived
   only Benjamini-Hochberg (q=0.041). On 39 tasks it is 7 (p=0.0156) and survives no correction.
2. **Metric definition.** Use function level, meaning the decoy in the top 5 functions. The module-or-function metric in
   `summary_p3.txt` also counts a decoy whose module is merely listed, which gives a clean count of 1 in some rows.
3. **Multiple testing.** There are 21 tests, 7 variants by 3 localizers. Bonferroni and Holm keep T4 on A1 and A2.
   Benjamini-Hochberg also keeps T4 on A1.5.
4. **Temperature 0 is not deterministic** on vLLM here. A1 shows up to 3 top-module changes in 39 with an unchanged
   prompt. Treat changes at or below that as noise.
5. **Gold labels and decoys have no recorded human validation.** The Y/N columns in
   `Phase1_Validation_and_Task_Set.xlsx` are empty. An earlier hand check of 15 tasks estimated label error at about 27
   percent.
6. Each trap variant was run once. The clean baselines were run once per session, and each trap file is paired with its
   own session's clean file.
7. Gold loss uses gold module in the top 3 on the clean run as the baseline, while headline accuracy is module at top 1.
   Clean A1 module at top 1 is 28 of 39 (71.8 percent) on the analysed tasks.
8. The 11 tasks with no hop distance have a decoy that is disconnected from gold in the call graph. It does not mean gold
   has no graph node.
9. Seven FastAPI tasks share the decoy `BackgroundTasks.add_task`, and pointer hosts repeat. None of those seven is a
   follower, so dropping them leaves the T3 pointer result unchanged. PR titles quoted in the traps sometimes name the gold
   function, which makes the attack conservative.
10. Notes placed inside the decoy are barely tested, because A2 read the decoy module in only 1 or 2 of 39 tasks.
11. The repo holds competition data in traces, Kaggle logs and problem text echoed in raw outputs. Check the competition
    licence before any public release. There is no LICENSE yet. Deleting files does not remove them from git history.
