### A. Frozen T4 run (Phase_3). How high the bait is ranked

| Loc | Bait in top 5 | Bait ranked first | Of those tasks, reference function in clean top 5 | Bait ranked above it | Reference function pushed out of top 5 |
|---|---|---|---|---|---|
| A1 | 13/39 | 12 | 0 | 0 | 0 |
| A1.5 | 9/39 | 8 | 4 | 4 | 4 |
| A2 | 11/39 | 10 | 7 | 6 | 5 |

### B. Control (T4c) against the bait (T4), 39 tasks

T4c is the bait built for another task of the same repo, with no name word in this issue. Same module and body as T4.
"T4 frozen" is the Phase_3 run in the paper. "T4 same session" is the rerun next to the control.

| Loc | T4c named | 95% CI | T4c ranked first | T4 frozen named | T4 same session named | T4 only | T4c only | McNemar p (T4 vs T4c) | paired with |
|---|---|---|---|---|---|---|---|---|---|
| A1 | 0/39 | 0.00-0.09 | 0 | 13/39 | 13/39 | 13 | 0 | 0.0002 | same session |
| A1.5 | 0/39 | 0.00-0.09 | 0 | 9/39 | 9/39 | 9 | 0 | 0.0039 | same session |
| A2 | 0/39 | 0.00-0.09 | 0 | 11/39 | 11/39 | 11 | 0 | 0.0010 | same session |

| Loc | Reference module lost under T4c | Top module changed under T4c |
|---|---|---|
| A1 | 1/29 | 2/39 |
| A1.5 | 0/34 | 0/39 |
| A2 | 0/31 | 0/39 |

### C. T4 replication. Same baits, new session

| Loc | Frozen run named | Same session named | Named in both | Only frozen | Only same session |
|---|---|---|---|---|---|
| A1 | 13/39 | 13/39 | 13 | 0 | 0 |
| A1.5 | 9/39 | 9/39 | 9 | 0 | 0 |
| A2 | 11/39 | 11/39 | 11 | 0 | 0 |

### C2. Same-session T4 run. How high the bait is ranked

| Loc | Bait in top 5 | Bait ranked first | Of those tasks, reference function in clean top 5 | Bait ranked above it | Reference function pushed out of top 5 |
|---|---|---|---|---|---|
| A1 | 13/39 | 12 | 0 | 0 | 0 |
| A1.5 | 9/39 | 8 | 4 | 4 | 4 |
| A2 | 11/39 | 10 | 7 | 6 | 5 |

### D. Where a keyword ranker (BM25 on the issue text) puts the bait, 39 tasks

B1 ranks on names only, B2 on names and source. No model involved.

| Bait | Ranker | Ranked first | In top 5 | Above every reference function | Median rank | No word in common with the issue |
|---|---|---|---|---|---|---|
| T4 | B1 | 30/39 | 35/39 | 35/39 | 1 | 0/39 |
| T4 | B2 | 20/39 | 30/39 | 32/39 | 1 | 0/39 |
| T4c | B1 | 0/39 | 0/39 | 2/39 | 721 | 14/39 |
| T4c | B2 | 0/39 | 2/39 | 4/39 | 249 | 2/39 |

| Loc | T4 named by the model | of which BM25 B1 also has the bait in its top 5 |
|---|---|---|
| A1 | 13 | 13 |
| A1.5 | 9 | 9 |
| A2 | 11 | 11 |

