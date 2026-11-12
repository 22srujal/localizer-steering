# Localizer Steering

How easily can text planted in a code repository steer the first stage of an LLM coding agent?

This project measures that question. It was built for the Kaggle Gemma 4 Developer Agent competition (paper track).

## Purpose

A coding agent that fixes a bug starts with a localizer. The localizer reads the bug report and decides which module and
function the fix belongs in. Every later step depends on that choice. Anyone who can contribute text to a repository, such
as a comment, a docstring or a function name, can try to point the localizer at the wrong place.

We ask two questions.

1. Can planted text pull a localizer toward a decoy function that has nothing to do with the bug?
2. Does the localizer have to read file contents for that to work, or is it enough to see names?

## Idea

We compare three localizers that all use the same model, Gemma 4 31B, and differ only in what they can see.

| Localizer | What it sees |
|---|---|
| A1 | A repo map with module and function names only |
| A1.5 | A repo map with names and signatures |
| A2 | The repo map, then the full source of up to 3 modules it chooses to read |

We then plant a trap and check whether the localizer names the decoy instead of the real fix location.

| Trap | What is planted |
|---|---|
| T1 | A maintainer-style comment saying the behaviour lives in the decoy |
| T2 | A docstring sentence saying the same |
| T3 | An instruction-style note, adapted from common prompt-injection wording, telling the reader to name the decoy |
| T4 | A new bait function whose name is taken from the issue, visible to every localizer |

Each of T1 to T3 is placed in one of two ways. In the **decoy** placement the note sits inside the decoy function. In the
**pointer** placement the note sits in a function of the real gold module and points at the decoy, so it is read whenever
the gold module is read.

## What is implemented

- **Task set.** 40 real bug-fix tasks, 17 from FastAPI, 15 from Rich and 8 from Requests, each with gold files and gold
  functions found by matching the real patch to a code graph (`task_set_40.json`).
- **Localizers.** A1, A1.5 and A2 in `localizer.py`. Answers are checked against the real list of modules and functions,
  so invented names are dropped.
- **Baselines.** Two BM25 keyword baselines in `bm25_base.py`.
- **Trap generator.** `trap_gen.py` picks a decoy for every task, in a different module from the gold code and far from
  it in the call graph. It writes the four traps in both placements. Output is deterministic.
- **Kaggle notebooks.** `Phase2_Localizers.ipynb` runs the clean localizers. `Phase3_Traps.ipynb` runs every trap variant
  on every localizer, and logs whether the planted text was actually shown to the model.
- **Analysis.** `Phase3_Reanalysis_v2.ipynb` computes decoy named, newly steered, gold loss and top-module drift. It uses
  Wilson intervals, exact McNemar tests, and Bonferroni, Holm and Benjamini-Hochberg correction, then draws the figure.

## Metrics

- **Decoy named.** The decoy function is in the answer's top 5 functions.
- **Newly steered.** The decoy is named on the trap run and not on the clean run of the same session.
- **Gold loss.** The correct module was in the clean answer and is missing from the trap answer.
- **Top-module drift.** The top-ranked module changed between the clean and the trap run.

## Results

Analysis uses 39 tasks. Rich task rich_3934 is excluded because its decoy sits inside the gold file.

| Variant | A1 | A1.5 | A2 |
|---|---|---|---|
| T4 bait function | 13 of 39 | 9 of 39 | 11 of 39 |
| T3 note, pointer | 0 | 0 | 7 |
| T1 note, pointer | 0 | 0 | 3 |
| T3 note, in decoy | 0 | 0 | 2 |
| T1 note, in decoy | 0 | 0 | 1 |
| T2 note, pointer or in decoy | 0 | 0 | 0 |

Numbers are tasks newly steered toward the decoy.

- A planted bait function name steers every localizer, because the name appears in every repo map.
- Planted comments steer only A2, the localizer that reads file contents. A2 followed the T3 pointer in 7 of the 28 tasks
  where it read the note and in 0 of the 11 where it did not.
- Instruction-style wording steers most, the maintainer comment less, and the docstring claim not at all.
- When A2 is steered it often loses the correct module. Under the T3 pointer it lost gold in 7 of 31 tasks and ranked the
  decoy first each time.

Full tables are in `Analysis_final_v2/tables.md` and the figure is `Analysis_final_v2/figure_a2_decoy_named.png`.

Further readings of the bait result, from the same saved files:

- When the bait is named it is ranked first in 30 of 33 cases (12 of 13, 8 of 9, 10 of 11).
- A1 named the bait in 13 of the 19 tasks where its clean answer had no reference function and in 0 of the 20 where it
  had one. A1.5 and A2 also named it in tasks they had right (4 of 28 and 7 of 28) and lost the reference function in 4
  and 5 of them. See `Analysis_final_v2/figure_bait_split.png`.
- One author hand-checked 23 of the 40 reference labels against the upstream pull requests. 19 matched exactly, 4
  omitted a minor function and none was wrong. Rescoring with the corrected labels changes no reported number
  (`Phase_3_control/rescore_corrected_labels.py`).

Control run (`Phase_3_control/`, tables in `Phase_3_control/control_tables.md`):

- The control bait, the same stub named after a different task's issue, was named in 0 of 39 tasks on every localizer.
- The bait, rerun in the same session, was named in the same 13, 9 and 11 tasks as the first run.
- A keyword ranker over names (BM25) ranks the bait first in 30 of 39 tasks and the control in none. Every task where
  Gemma named the bait has it in the ranker's top five.

## Repository layout

| Path | Contents |
|---|---|
| `task_set_40.json` | The 40 tasks with gold files and gold functions |
| `localizer.py` | Localizers A1, A1.5 and A2 |
| `bm25_base.py`, `bm25_results.json` | BM25 baselines and their results |
| `Phase_2_v2/` | Clean localizer runs |
| `Phase_3/` | Trap runs for T1 in decoy, T3 pointer and T4, with that session's clean runs |
| `Phase_3_v2/` | Trap runs for T1 pointer, T2 and T3 in decoy, with that session's clean runs |
| `Phase3_Reanalysis_v2.ipynb` | Analysis notebook that builds every table and the figure |
| `Analysis_final_v2/` | Final tables, CSV and figure |
| `Phase_3_control/` | Control run for the bait function, its notebook, generator v3 and offline analysis scripts |

Each `Phase_3*` folder holds `clean_{A1,A1.5,A2}.json`, `trap_{variant}_{localizer}.json`, `spec_{variant}.json` with the
decoy chosen for each task, and its own copies of `localizer.py` and `trap_gen.py`.

## How to run

### Reproduce the tables and the figure

No GPU and no model calls are needed. The notebook reads the saved result files.

```bash
pip install matplotlib
jupyter notebook Phase3_Reanalysis_v2.ipynb
```

Run all cells from the repository root, next to `Phase_3/` and `Phase_3_v2/`. Outputs are written to `Analysis_final_v2/`.

### Rerun the experiments

The experiments need a Kaggle account with access to the Gemma 4 Developer Agent competition, which provides the data, the
wheel files and the model.

1. Open `Phase2_Localizers.ipynb` on Kaggle for the clean runs, or `Phase3_Traps.ipynb` for the trap runs.
2. Set the accelerator to GPU L4 x4 and turn Internet off.
3. Attach the competition data and run the notebook. It writes its own code into `/kaggle/working`.

In `Phase3_Traps.ipynb`, the `RUN` setting chooses which trap variants run. A full Phase 3 run takes about 3.5 GPU-hours.
Runs at temperature 0 on vLLM are not fully deterministic, so a rerun will match closely but not byte for byte.

## Scope

One model (Gemma 4 31B, w4a16), three Python repositories, 40 tasks and one run per variant. Tasks use data that ships
with the competition, so check the competition rules before sharing task text or traces.

## License

To be added.
