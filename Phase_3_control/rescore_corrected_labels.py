"""Does correcting the three partial reference labels change any number in the paper?

The hand check found three labels in the 39 analysis tasks that omit a minor function the fix also touched.
This script rescores the saved answers with the corrected labels. No model calls, frozen files only.
    python Phase_3_control/rescore_corrected_labels.py
"""
import copy, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCL = 'rich_3934'
ORIG = {t['id']: t for t in json.load(open(ROOT / 'task_set_40.json')) if t['id'] != EXCL}
FIX = copy.deepcopy(ORIG)
FIX['rich_3782']['gold_functions'] = [f for f in FIX['rich_3782']['gold_functions'] if not f.endswith('guess_lexer')] + \
    ['rich.syntax.PaddingProperty.__get__', 'rich.syntax.PaddingProperty.__set__']
FIX['requests_7505']['gold_functions'] += ['requests._types.has_read']; FIX['requests_7505']['gold_files'] += ['src/requests/_types.py']
FIX['fastapi_14512']['gold_functions'] += ['fastapi._compat.v2.asdict']

norm = lambda n: n[4:] if n.startswith('src.') else n
rk = lambda lst, gold: next((i + 1 for i, x in enumerate(lst) if x in gold), None)


def score(path, tasks):
    out = {}
    for r in json.load(open(path)):
        if r['id'] == EXCL: continue
        t = tasks[r['id']]; gf = {norm(x) for x in t['gold_functions']}
        gm = {norm(re.sub(r'\.py$', '', x).replace('/', '.')).replace('.__init__', '') for x in t['gold_files']}
        out[r['id']] = dict(m=rk(r['modules'], gm), f=rk(r['functions'], gf), d=r.get('decoy_fn_rank'))
    return out


def numbers(tasks):
    n = []
    for folder in ('Phase_3', 'Phase_3_v2'):
        for a in ('A1', 'A1.5', 'A2'):
            c = score(ROOT / folder / f'clean_{a}.json', tasks)
            n.append((folder, a, 'clean', sum(v['m'] == 1 for v in c.values()), sum(1 for v in c.values() if v['m']),
                      sum(v['f'] == 1 for v in c.values()), sum(1 for v in c.values() if v['f'])))
            for p in sorted((ROOT / folder).glob(f'trap_*_{a}.json')):
                t = score(p, tasks); named = [i for i in t if t[i]['d']]; base = [i for i in c if c[i]['m']]
                n.append((folder, a, p.stem, len(named), sum(1 for i in base if not t[i]['m']), len(base),
                          sum(1 for i in named if c[i]['f']), sum(1 for i in named if c[i]['f'] and not t[i]['f']),
                          sum(1 for i in c if c[i]['f'] and t[i]['d']), sum(1 for i in c if not c[i]['f'] and t[i]['d'])))
    return n


a, b = numbers(ORIG), numbers(FIX)
diff = [(x, y) for x, y in zip(a, b) if x != y]
print(f'{len(a)} rows compared (clean accuracy, steering, reference loss, bait split) across both sessions')
print('rows that change with the corrected labels:', len(diff))
for x, y in diff: print('  was', x, '\n  now', y)
