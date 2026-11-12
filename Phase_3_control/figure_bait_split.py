"""Fig. 2. Bait function (T4) split by whether the clean answer already held a reference function.
Reads the frozen Phase_3 files only. Writes Analysis_final_v2/figure_bait_split.png.
    python Phase_3_control/figure_bait_split.py
"""
import json, math
from pathlib import Path
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
EXCL = 'rich_3934'
LOCS = [('A1', 'A1\nnames only'), ('A1.5', 'A1.5\n+ signatures'), ('A2', 'A2\nreads modules')]
BLUE, ORANGE, INK, MUTED, GRID, SURF = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'


def rows(p): return {r['id']: r for r in json.load(open(p)) if r['id'] != EXCL}


def wilson(k, n, z=1.959963984540054):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - a) / d), min(1.0, (c + a) / d)


data = []
for a, _ in LOCS:
    C = rows(ROOT / 'Phase_3' / f'clean_{a}.json'); T = rows(ROOT / 'Phase_3' / f'trap_T4_decoy_{a}.json')
    miss = [i for i in C if not C[i]['fn_rank']]; hit = [i for i in C if C[i]['fn_rank']]
    data.append(((sum(1 for i in miss if T[i]['decoy_fn_rank']), len(miss)), (sum(1 for i in hit if T[i]['decoy_fn_rank']), len(hit))))
    print(a, data[-1])

fig, ax = plt.subplots(figsize=(9, 4.6), dpi=200); fig.patch.set_facecolor(SURF); ax.set_facecolor(SURF)
w = 0.34
for x, (m, h) in enumerate(data):
    for off, (k, n), col in ((-w / 2 - 0.02, m, ORANGE), (w / 2 + 0.02, h, BLUE)):
        p = k / n; lo, hi = wilson(k, n)
        ax.bar(x + off, p * 100, w, color=col, zorder=3)
        ax.errorbar(x + off, p * 100, yerr=[[(p - lo) * 100], [(hi - p) * 100]], color=INK, capsize=4, lw=1.4, zorder=4)
        ax.text(x + off, hi * 100 + 2.5, f'{k}/{n}', ha='center', va='bottom', fontsize=11, color=INK)
ax.set_xticks(range(3)); ax.set_xticklabels([l for _, l in LOCS], fontsize=11, color=INK)
ax.set_ylim(0, 100); ax.set_yticks(range(0, 101, 20)); ax.set_yticklabels([f'{v}%' for v in range(0, 101, 20)], color=MUTED)
ax.set_ylabel('Tasks where the bait was named', color=MUTED, fontsize=11)
ax.yaxis.grid(True, color=GRID, lw=1, zorder=0); ax.set_axisbelow(True)
for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(MUTED); ax.tick_params(length=0)
ax.set_title('Bait function (T4): who takes it depends on what the clean answer held', loc='left', fontsize=12.5, color=INK, fontweight='bold', pad=14)
h = [plt.Rectangle((0, 0), 1, 1, color=ORANGE), plt.Rectangle((0, 0), 1, 1, color=BLUE)]
ax.legend(h, ['Clean answer had no reference function', 'Clean answer had a reference function'], loc='upper right', frameon=False, fontsize=10.5)
fig.text(0.01, 0.01, '39 tasks. Error bars are 95% Wilson intervals.', fontsize=9, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 1))
out = ROOT / 'Analysis_final_v2' / 'figure_bait_split.png'; fig.savefig(out, facecolor=SURF); print('wrote', out)
