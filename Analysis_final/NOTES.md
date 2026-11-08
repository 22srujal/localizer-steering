# Notes on reproduction

What `analyze_final.py` could and could not reproduce from the saved files. No GPU or API calls were made.

## Reproduced exactly

- Every module-level count in item 1 (clean, trap, up, down) and every gold-loss and drift number in item 6 matches
  `trap_gen.analyze`, and therefore `Phase_3/summary_p3.txt` and `Phase_3_v2/summary_p3.txt`. The script asserts this.
- All 84 McNemar p-values (21 tests × {function, module} × {all 40, without rich_3934}) match an independent exact
  binomial test in rational arithmetic and `trap_gen.mcnemar`, to within 1e-12.
- Every number in AUDIT.md §3 that can be derived from the Phase 3 files reproduces, including:
  - clean module@1 29/34/32
  - A2 T3 pointer 1→9 (module) and 0→8 (function), and the rich_3934 sensitivity 0.0078 → 0.0156
  - T1 pointer sensitivity 1→4, p = 0.25
  - T4 A1 sensitivity 1→13, p = 0.0005
  - the 29 identical seen sets and the 8/4/0 followers
  - Fisher 0.0045
  - all 7 A2 T3-pointer gold losses have the decoy at rank 1 (function and module)
  - A1 noise floor 3, 2, 2, 0, 1, 1
  - session-to-session differences of 2/3 raw texts and 1/1 function lists
  - Phase 2 A1 31 and 30, A1.5 34 at module@1 and 35 at module@3

## Could not reproduce or could not check, and why

| Number or claim | Status | Why |
|---|---|---|
| Handover "clean A1 = 72%" | Not reproduced as a count | The true value is 29/40 = 72.5%. 72% is a float display. The tables use 29/40. |
| Handover "A1.5 leads on modules 35 vs 32, p = 0.25" | Not reproduced at module@1 | 35 is module@3. At module@1 (the headline metric) it is 34 vs 32. Not recomputed here (Phase 2, outside this analysis); see AUDIT F6. |
| Handover "only T3 pointer and T4 hold up after correction" | Not reproduced | With m = 21, Bonferroni and Holm keep only T4 A1 and T4 A2. BH keeps T3 pointer A2 (q = 0.041) and all three T4 tests. **With rich_3934 excluded, T3 pointer A2 fails BH too (q = 0.082).** |
| Handover "Fisher p = 0.004" for T3 vs T2 | Reproduced (0.0045), but superseded | The tasks are paired. The correct McNemar test gives p = 0.0078. |
| Hop distances, "11 tasks without a graph node" | Not checkable | Needs the graph files, which are only on Kaggle. Spec `meta` has `hops = null` for 11 tasks. |
| Decoy BM25 rank and the "smallest module in top 5" rule | Not checkable | Needs the graph files. |
| Decoy file paths (item 2) | Checked by a proxy | The specs store dotted ids, not file paths. A decoy counts as being in a gold file when its dotted id starts with that gold file's module path (no task has an `__init__.py` gold file, so this proxy has no ambiguity here). Only rich_3934 is flagged, for both the T1–T3 decoy and the T4 bait. A graph-based check of file paths on Kaggle would confirm it. |
| "A1 (and A1.5) get a byte-identical prompt under T1–T3" (noise floor) | Not checkable byte-for-byte | Based on reading the code: A1's map lists names only, and A1.5's `signature()` reads only the `def` line(s), above where notes are planted. Rebuilding the prompts needs the graphs. |
| Part 1 hop numbers (44%, 27%, 91%, 86%) | Not reproducible | No script or output in the repo (AUDIT §7). |
| BM25 baseline under traps (plan: "whether B2 drifts") | Not available | No trap BM25 runs exist (AUDIT F14). |

## Additions not in AUDIT.md

- Function level also moves for **T3 decoy A2 (0→2, p = 0.50)** and **T1 decoy A2 (0→1)**. AUDIT F5 lists function-level counts only for the pointer variants and T4. Neither is significant.
- At function level, T4 A1 is 0→14 with **p = 0.00012**. The 0.00024 in AUDIT is the module-level value (1→14).
- In every variant the module-level count equals `trap_gen.named_decoy` (function OR module). A function hit never happens without the module also being named.
- Leave-one-decoy-out (A2 T3 pointer): none of the 7 BackgroundTasks tasks is a follower, so dropping them leaves 0→8, p = 0.0078 (n = 33). Dropping any single decoy gives at most p = 0.0156.
- A2 never named the pointer decoy at function level in a task where it did not read the note (0/11 for each pointer variant).
- Clean vs clean across the two sessions: top-1 module identical for all 40 tasks for all three localizers. The module list differs in 1 A1 task, at a lower rank.

## Method details that affect the numbers slightly

- The Wilson intervals use z = 1.95996 rather than 1.96, and are clamped to [0, 1]. Values agree with `trap_gen.wilson` to 2 decimals.
- Gold loss uses module in the top 3 on the clean run as the denominator (30/35/32), not module@1, to match `trap_gen.analyze`.
