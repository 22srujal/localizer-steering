"""Tables for the bait control (T4c), the T4 replication and the BM25 bait ranks.

Reads saved result files only. No GPU, no model calls.
    python Phase_3_control/analyze_control.py            (results expected in Phase_3_control/)
    python Phase_3_control/analyze_control.py some_dir   (results somewhere else)
Part A needs only the frozen Phase_3 files, so it works before the control run exists.
Parts B to D need the files that Phase3_Control.ipynb writes.
Everything is at function level (bait in the top 5 functions) on the 39 analysis tasks, rich_3934 excluded.
Writes control_tables.md next to the results.
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'Phase_3_control'
EXCL = 'rich_3934'; LOCS = ['A1', 'A1.5', 'A2']
out = []


def rows(p):
    return {r['id']: r for r in json.load(open(p)) if r['id'] != EXCL}


def wilson(k, n, z=1.959963984540054):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - a) / d), min(1.0, (c + a) / d))


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def strict(C, T):
    """How strongly the bait is ranked, and what happened to the reference function, in one trap run."""
    named = [r for r in T.values() if r['decoy_fn_rank']]
    first = [r for r in named if r['decoy_fn_rank'] == 1]
    had = [r for r in named if C[r['id']]['fn_rank']]            # reference function was in the clean top 5
    above = [r for r in had if r['fn_rank'] is None or r['decoy_fn_rank'] < r['fn_rank']]
    dropped = [r for r in had if r['fn_rank'] is None]
    return len(named), len(first), len(had), len(above), len(dropped)


def strict_table(title, folder, variant):
    out.append(f'### {title}\n')
    out.append('| Loc | Bait in top 5 | Bait ranked first | Of those tasks, reference function in clean top 5 | Bait ranked above it | Reference function pushed out of top 5 |')
    out.append('|---|---|---|---|---|---|')
    for a in LOCS:
        C = rows(folder / f'clean_{a}.json'); T = rows(folder / f'trap_{variant}_{a}.json')
        n, f, h, ab, dr = strict(C, T)
        out.append(f'| {a} | {n}/{len(T)} | {f} | {h} | {ab} | {dr} |')
    out.append('')


# ---------- A. frozen Phase 3 T4 run ----------
strict_table('A. Frozen T4 run (Phase_3). How high the bait is ranked', ROOT / 'Phase_3', 'T4_decoy')

have = lambda v: all((RES / f'trap_{v}_{a}.json').exists() for a in LOCS)
if not have('T4c_decoy'):
    out.append(f'Control results not found in {RES}. Parts B to D skipped.')
else:
    # ---------- B. control against bait ----------
    rep = have('T4_decoy')
    out.append('### B. Control (T4c) against the bait (T4), 39 tasks\n')
    out.append('T4c is the bait built for another task of the same repo, with no name word in this issue. Same module and body as T4.')
    out.append('"T4 frozen" is the Phase_3 run in the paper. "T4 same session" is the rerun next to the control.\n')
    out.append('| Loc | T4c named | 95% CI | T4c ranked first | T4 frozen named | T4 same session named | T4 only | T4c only | McNemar p (T4 vs T4c) | paired with |')
    out.append('|---|---|---|---|---|---|---|---|---|---|')
    for a in LOCS:
        Tc = rows(RES / f'trap_T4c_decoy_{a}.json'); Tf = rows(ROOT / 'Phase_3' / f'trap_T4_decoy_{a}.json')
        Ts = rows(RES / f'trap_T4_decoy_{a}.json') if rep else None
        P = Ts or Tf
        kc = sum(1 for r in Tc.values() if r['decoy_fn_rank']); lo, hi = wilson(kc, len(Tc))
        b = sum(1 for i in P if P[i]['decoy_fn_rank'] and not Tc[i]['decoy_fn_rank'])
        c = sum(1 for i in P if Tc[i]['decoy_fn_rank'] and not P[i]['decoy_fn_rank'])
        out.append(f"| {a} | {kc}/{len(Tc)} | {lo:.2f}-{hi:.2f} | {sum(1 for r in Tc.values() if r['decoy_fn_rank'] == 1)} | "
                   f"{sum(1 for r in Tf.values() if r['decoy_fn_rank'])}/{len(Tf)} | "
                   f"{'-' if not rep else str(sum(1 for r in Ts.values() if r['decoy_fn_rank'])) + '/' + str(len(Ts))} | {b} | {c} | {mcnemar(b, c):.4f} | "
                   f"{'same session' if rep else 'frozen run'} |")
    out.append('')
    out.append('| Loc | Reference module lost under T4c | Top module changed under T4c |')
    out.append('|---|---|---|')
    for a in LOCS:
        C = rows(RES / f'clean_{a}.json'); Tc = rows(RES / f'trap_T4c_decoy_{a}.json')
        base = [i for i in C if C[i]['mod_rank']]; lost = [i for i in base if not Tc[i]['mod_rank']]
        top = lambda r: (r['modules'] or [None])[0]
        out.append(f"| {a} | {len(lost)}/{len(base)} | {sum(1 for i in C if top(C[i]) != top(Tc[i]))}/{len(C)} |")
    out.append('')

    # ---------- C. replication ----------
    if rep:
        out.append('### C. T4 replication. Same baits, new session\n')
        out.append('| Loc | Frozen run named | Same session named | Named in both | Only frozen | Only same session |')
        out.append('|---|---|---|---|---|---|')
        for a in LOCS:
            Tf = rows(ROOT / 'Phase_3' / f'trap_T4_decoy_{a}.json'); Ts = rows(RES / f'trap_T4_decoy_{a}.json')
            f = {i for i in Tf if Tf[i]['decoy_fn_rank']}; s = {i for i in Ts if Ts[i]['decoy_fn_rank']}
            out.append(f'| {a} | {len(f)}/{len(Tf)} | {len(s)}/{len(Ts)} | {len(f & s)} | {len(f - s)} | {len(s - f)} |')
        out.append('')
        strict_table('C2. Same-session T4 run. How high the bait is ranked', RES, 'T4_decoy')

    # ---------- D. BM25 ----------
    if (RES / 'bm25_bait.json').exists():
        BM = [r for r in json.load(open(RES / 'bm25_bait.json')) if r['id'] != EXCL]
        out.append('### D. Where a keyword ranker (BM25 on the issue text) puts the bait, 39 tasks\n')
        out.append('B1 ranks on names only, B2 on names and source. No model involved.\n')
        out.append('| Bait | Ranker | Ranked first | In top 5 | Above every reference function | Median rank | No word in common with the issue |')
        out.append('|---|---|---|---|---|---|---|')
        for tr in ('T4', 'T4c'):
            for tag in ('B1', 'B2'):
                x = [r[f'{tr}_{tag}'] for r in BM]; rk = sorted(v['bait_rank'] for v in x)
                out.append(f"| {tr} | {tag} | {sum(1 for v in rk if v == 1)}/{len(x)} | {sum(1 for v in rk if v <= 5)}/{len(x)} | "
                           f"{sum(1 for v in x if v['gold_rank'] is None or v['bait_rank'] < v['gold_rank'])}/{len(x)} | {rk[len(rk) // 2]} | "
                           f"{sum(1 for v in x if not v['bait_score'])}/{len(x)} |")
        out.append('')
        # does the model follow the bait where BM25 would too?
        out.append('| Loc | T4 named by the model | of which BM25 B1 also has the bait in its top 5 |')
        out.append('|---|---|---|')
        b1 = {r['id']: r['T4_B1']['bait_rank'] for r in BM}
        for a in LOCS:
            Tf = rows(ROOT / 'Phase_3' / f'trap_T4_decoy_{a}.json'); nm = [i for i in Tf if Tf[i]['decoy_fn_rank']]
            out.append(f'| {a} | {len(nm)} | {sum(1 for i in nm if b1.get(i) and b1[i] <= 5)} |')
        out.append('')

txt = '\n'.join(out); print(txt)
(RES if RES.exists() else ROOT / 'Phase_3_control').joinpath('control_tables.md').write_text(txt + '\n')
