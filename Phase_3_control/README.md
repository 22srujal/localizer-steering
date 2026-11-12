# Phase 3 control run

Added 12 Nov. Nothing outside this folder was changed, and every frozen result still maps to the code that made it.

| File | What it is |
|---|---|
| `Phase3_Control.ipynb` | Kaggle notebook. Run top to bottom, nothing to edit. About 70 minutes of model time after the server starts. |
| `trap_gen.py` | Trap generator v3. Same as `Phase_3_v2/trap_gen.py` plus the T4c control and a BM25 bait-rank helper. Decoy choice and T1 to T4 are untouched. |
| `localizer.py`, `task_set_40.json` | Unchanged copies of the frozen files. |
| `analyze_control.py` | Offline tables from the saved results. Part A already works on the frozen Phase_3 files. |
| `control_tables.md` | Output of the script. |

## What the run adds

- **T4c, the control for the bait.** For each task, the bait built for a different task of the same repo is planted in
  the same module with the same body. Its name words do not occur in this task's issue. If the model names it, adding
  any `handle_` function is enough. If it does not, the T4 effect is due to the issue words in the name.
- **T4 again in the same session**, so the bait and its control are compared within one session and the headline
  count is replicated once.
- **BM25 bait ranks**, no model calls. Shows whether a plain keyword ranker would also put the bait at the top.

## After the run

Download `clean_*.json`, `trap_T4c_decoy_*.json`, `trap_T4_decoy_*.json`, `spec_T4c_decoy.json`, `spec_T4_decoy.json`,
`bm25_bait.json` and `summary_control.txt` from `/kaggle/working` into this folder, then

```bash
python Phase_3_control/analyze_control.py
```

## Other scripts here (no GPU, frozen files only)

| File | What it does |
|---|---|
| `figure_bait_split.py` | Draws `Analysis_final_v2/figure_bait_split.png`, the bait result split by clean outcome. |
| `rescore_corrected_labels.py` | Rescores every saved run with the three corrected reference labels and reports what changes (nothing). |
