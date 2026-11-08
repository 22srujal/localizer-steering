# localizer-steering

Can planted text in a repository (comments, docstrings, instruction-style notes, bait functions) steer the
localization stage of an LLM coding agent toward a decoy function? Study on 40 tasks (17 FastAPI, 15 Rich,
8 Requests) with Gemma 4 31B (QAT w4a16) on Kaggle, temperature 0. Three localizers:

- **A1**: repo map, names only
- **A1.5**: repo map, names and signatures
- **A2**: repo map, then reads up to 3 modules

## Canonical folders

| Folder | Role | Canonical? |
|---|---|---|
| `Phase_3/` | Trap runs, pilot session: T1 decoy, T3 pointer, T4, plus that session's clean runs | **Yes** (traps) |
| `Phase_3_v2/` | Trap runs, rest session: T1 pointer, T2 decoy, T2 pointer, T3 decoy, plus that session's clean runs | **Yes** (traps) |
| `Phase_2_v2/` | Clean localizer runs with the fixed localizer | **Yes** (Phase 2 clean table) |
| `Phase_2/` | First clean runs. `loc_A2.json` comes from the old, buggy A2 | Historical |
| `Analysis_final/` | Final paper tables, CSV, figure and notes, made from the files above | **Yes** (analysis) |
| repo root | Agent-harness check (`trace_*.json`), BM25 baselines, shared code copies | Mixed |

Frozen files (do not edit): every `Phase_3*/` result and spec file, `Phase_2*/loc_*.json`, `bm25_results.json`,
`task_set_40.json`, and both `trap_gen.py` files.

## What each result file is

| File | Contents |
|---|---|
| `task_set_40.json` (identical copies in `Phase_2_v2/`, `Phase_3/`, `Phase_3_v2/`) | The 40 tasks with gold functions and gold files |
| `Phase_3*/clean_{A1,A1.5,A2}.json` | Clean run for that session. One row per task: answer modules and functions, gold ranks, A2 `shown` nodes |
| `Phase_3*/trap_{variant}_{loc}.json` | The same rows under a trap, plus `decoy_fn_rank`, `decoy_mod_rank` and, for A2, `trap_seen` (A2 read the planted text) |
| `Phase_3*/spec_{variant}.json` | Decoy (or bait) id per task, host node of the planted text, and `meta` (hops, placement) |
| `Phase_3*/summary_p3.txt` | Printed summary from `trap_gen.analyze` (module-level metric) |
| `Phase_3*/timing.json`, `*.log` | Run times, model path, Kaggle session logs |
| `Phase_2*/loc_*.json`, `summary*.txt` | Clean Phase 2 localizer runs. `loc_A2_v2.json` is the fixed A2 rerun, `loc_A1_rerun.json` is the A1 noise rerun |
| `Phase_2/localizer_v1_buggy.py` | Old localizer restored from commit `a7c2c22`. It produced `Phase_2/loc_A2.json` |
| `bm25_results.json` | BM25 baselines B1 and B2 (clean only), from `bm25_base.py` |
| `Analysis_final/tables.md` | All final tables (decoy named, sensitivity, multiple-testing correction, pointer comparison, leave-one-decoy-out, gold loss and drift, clean accuracy) |
| `Analysis_final/all_results.csv` | One row per variant × localizer with every metric |
| `Analysis_final/figure_a2_decoy_named.png` | A2 decoy named (function level) for the comment variants, plus T4 for all localizers |
| `Analysis_final/NOTES.md` | Numbers that could not be reproduced or checked, and why |

## Rerunning the analysis (no GPU)

```bash
pip install matplotlib        # only needed for the figure
python Analysis_final/analyze_final.py
```

The script reads only saved JSON files and imports the frozen `Phase_3_v2/localizer.py` and `trap_gen.py` read-only.
It asserts that it reproduces `trap_gen.analyze` and checks every p-value against an independent exact binomial test.

Rerunning the experiments themselves needs Kaggle (the competition data, the wheelhouse and the model). The
notebooks `Phase_3*/Phase3_Traps.ipynb` write their own code into `/kaggle/working`. Set `RUN` in `Phase_3_v2`.
A full Phase 3 rerun takes about 3.5 GPU-hours on L4×4, and it will not reproduce byte-for-byte (see caveats).

## Known caveats (from AUDIT.md)

1. **rich_3934's decoy is in a gold file** (`rich.live._RefreshThread.run` is in `rich/live.py`). `module_of_node`
   misses private classes. Report the sensitivity rows without this task. Without it, A2 T3 pointer goes from
   p = 0.0078 to 0.0156 and no longer survives BH correction.
2. **Metric definition.** `summary_p3.txt` counts "decoy named" as function OR module. Use function level for the paper.
   Clean baselines are 0/40 at function level.
3. **Multiple testing.** There are 21 tests. Bonferroni and Holm keep only T4 A1 and T4 A2. BH also keeps T4 A1.5
   and T3 pointer A2 (the latter only with rich_3934 included).
4. **Temperature 0 is not deterministic** on vLLM here. A1 shows up to 3/40 top-module changes with an unchanged
   prompt. Treat changes at or below 3/40 as noise.
5. **Gold labels have no recorded human validation.** The Y/N columns in `Phase1_Validation_and_Task_Set.xlsx` are empty.
6. Each trap variant was run once. The clean baselines were run once per session, and each trap file is paired with
   its own session's clean file.
7. Gold loss uses module-in-top-3 as the clean baseline, while headline accuracy is module@1.
   Clean A1 is 29/40 (72.5%), not 72%.
8. "11 tasks without a hop distance" means the decoy is **disconnected** from gold in the call graph, not that gold has no node.
9. 7 FastAPI tasks share the decoy `BackgroundTasks.add_task`. Pointer hosts repeat. PR titles quoted in the traps
   sometimes name the gold function, which makes the attack conservative.
10. The repo holds competition data (traces, logs, problem text in raw outputs). Check the competition licence before
    any public release. There is no LICENSE yet.
