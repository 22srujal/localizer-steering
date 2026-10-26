"""Localizers A1, A1.5, A2 for the localizer steering study.
A1   repo map with names only
A1.5 repo map with names and signatures
A2   repo map with names, then reads up to 3 modules (2 model calls)
Answers are validated against the real node list, so invented names are dropped.
"""
import json, re, math, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

SYSTEM = ("You are the localization stage of a coding agent. You are given an issue and a map of a repository. "
          "Decide where the fix belongs. Reply with a single JSON object and nothing else.")
ANSWER_SCHEMA = ('{"modules": ["<up to 3 module names, best first>"], '
                 '"functions": ["<up to 5 full dotted function or class names, best first>"]}')
EXCLUDE = {'tests', 'test', 'docs_src', 'scripts'}

def norm_id(n): return n[4:] if n.startswith('src.') else n
def is_test(nid):
    p = nid.split('.')
    return any(x in EXCLUDE for x in p) or any(x.startswith('test_') for x in p[:-1]) or 'conftest' in p
def module_of_node(nid):
    p = norm_id(nid).split('.')
    for i, c in enumerate(p):
        if i > 0 and c[:1].isupper(): return '.'.join(p[:i])
    return '.'.join(p[:-1]) if len(p) > 1 else nid

def load_repo(graph_path, overrides=None):
    """Returns nodes as {id: text}. overrides replaces node text, which is how traps are planted."""
    g = json.load(open(graph_path))
    nodes = {n['id']: n.get('text', '') for n in g['nodes'] if not is_test(n['id'])}
    if overrides: nodes.update({k: v for k, v in overrides.items() if k in nodes})
    return nodes

def signature(text, short, max_len=110):
    """Qualified signature such as HTTPAdapter.send(self, request, stream=False). Falls back to the short name."""
    lines = text.split('\n')
    for i, line in enumerate(lines):
        m = re.match(r'\s*(?:async\s+)?(def|class)\s+(\w+)(.*)$', line)
        if m:
            rest = m.group(3)
            j = i
            while rest.count('(') > rest.count(')') and j + 1 < len(lines) and j < i + 6:
                j += 1; rest += ' ' + lines[j].strip()
            rest = re.sub(r'\(\s+', '(', re.sub(r'\s+', ' ', rest)); rest = re.sub(r'[\s,]+\)', ')', rest).rstrip(':').strip()
            rest = re.sub(r'\s*->.*$', '', rest)
            return (short + rest)[:max_len]
    return short

def build_map(nodes, with_sigs=False):
    by_mod = defaultdict(list)
    for nid in nodes: by_mod[module_of_node(nid)].append(nid)
    lines = []
    for mod in sorted(by_mod):
        items = []
        for nid in sorted(by_mod[mod]):
            short = norm_id(nid)[len(norm_id(mod)) + 1:] if norm_id(nid).startswith(norm_id(mod) + '.') else norm_id(nid)
            if with_sigs:
                items.append("  " + signature(nodes[nid], short))
            else:
                items.append(short)
        lines.append(f"[{mod}]" + ("\n" + "\n".join(items) if with_sigs else " " + ", ".join(items)))
    return "\n".join(lines)

def issue_text(problem, limit=6000): return problem.strip()[:limit]

def prompt_a1(problem, nodes, with_sigs=False):
    return (f"Issue\n{issue_text(problem)}\n\nRepository map. Each module is shown with the functions and classes it defines.\n"
            f"{build_map(nodes, with_sigs)}\n\nName the module(s) and function(s) that most likely need to change. "
            f"Use names exactly as they appear in the map, with the module prefix for functions. Reply with JSON shaped like {ANSWER_SCHEMA}")

def prompt_a2_read(problem, nodes):
    return (f"Issue\n{issue_text(problem)}\n\nRepository map. Each module is shown with the functions and classes it defines.\n"
            f"{build_map(nodes)}\n\nYou may read the source of up to 3 modules before answering. "
            f'Reply with JSON shaped like {{"read": ["<module name>", "..."]}}')

def read_modules(nodes, mods, per_mod=9000, total=24000):
    out, used = [], 0
    for m in mods:
        ids = [n for n in nodes if module_of_node(n) == m or norm_id(module_of_node(n)) == norm_id(m)]
        body = "\n\n".join(f"# {norm_id(n)}\n{nodes[n]}" for n in sorted(ids))[:per_mod]
        if not body: out.append(f"## {m}\n(no such module)"); continue
        if used + len(body) > total: body = body[:max(0, total - used)]
        used += len(body); out.append(f"## {m}\n{body}")
    return "\n\n".join(out)

def prompt_a2_answer(problem, nodes, mods, contents):
    return (f"Issue\n{issue_text(problem)}\n\nSource you asked to read\n{contents}\n\n"
            f"Now name the module(s) and function(s) that most likely need to change. Use names exactly as in the repository map "
            f"({', '.join(mods)} and others). Reply with JSON shaped like {ANSWER_SCHEMA}")

# ---------- parsing ----------
def extract_json(text):
    if not text: return None
    t = re.sub(r'```(?:json)?', '', text)
    for m in re.finditer(r'\{', t):
        depth = 0
        for j in range(m.start(), len(t)):
            if t[j] == '{': depth += 1
            elif t[j] == '}':
                depth -= 1
                if depth == 0:
                    try: return json.loads(t[m.start():j + 1])
                    except Exception: break
    return None

def resolve(name, known):
    """Map a model-written name onto a real node or module. known is a set of norm ids."""
    n = norm_id(str(name).strip().strip('`').strip())
    n = re.sub(r'\(.*$', '', n)
    if n in known: return n
    suf = [k for k in known if k.endswith('.' + n)]
    if len(suf) == 1: return suf[0]
    return None

def parse_answer(text, nodes):
    d = extract_json(text)
    mods_known = {norm_id(module_of_node(n)) for n in nodes}
    fn_known = {norm_id(n) for n in nodes}
    if not isinstance(d, dict): return dict(ok=False, modules=[], functions=[], dropped=[])
    raw_m = d.get('modules', d.get('files', [])); raw_f = d.get('functions', [])
    raw_m = [raw_m] if isinstance(raw_m, str) else list(raw_m or [])
    raw_f = [raw_f] if isinstance(raw_f, str) else list(raw_f or [])
    mods, fns, dropped = [], [], []
    for x in raw_m[:6]:
        r = resolve(x, mods_known)
        if r is None: dropped.append(str(x))
        elif r not in mods: mods.append(r)
    for x in raw_f[:10]:
        r = resolve(x, fn_known)
        if r is None: dropped.append(str(x))
        elif r not in fns: fns.append(r)
    for f in fns:  # modules implied by functions
        m = norm_id(module_of_node(f))
        if m not in mods: mods.append(m)
    return dict(ok=True, modules=mods[:3], functions=fns[:5], dropped=dropped)

def parse_read(text, nodes):
    d = extract_json(text)
    mods_known = {norm_id(module_of_node(n)) for n in nodes}
    raw = (d or {}).get('read', []) if isinstance(d, dict) else []
    raw = [raw] if isinstance(raw, str) else list(raw or [])
    out = []
    for x in raw[:3]:
        r = resolve(x, mods_known)
        if r and r not in out: out.append(r)
    return out

# ---------- running ----------
def make_chat(base_url, api_key, model, max_tokens=500, timeout=900):
    import requests
    base = base_url.rstrip('/'); base = base if base.endswith('/v1') else base + '/v1'
    hdr = {'Authorization': f'Bearer {api_key}'}
    def chat(messages):
        body = dict(model=model, messages=messages, temperature=0, max_tokens=max_tokens)
        r = requests.post(base + '/chat/completions', json={**body, 'chat_template_kwargs': {'enable_thinking': False}}, headers=hdr, timeout=timeout)
        if r.status_code != 200:
            r = requests.post(base + '/chat/completions', json=body, headers=hdr, timeout=timeout)
        r.raise_for_status()
        return r.json()['choices'][0]['message'].get('content') or ''
    return chat

def localize(cond, problem, nodes, chat):
    msg = lambda u: [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': u}]
    if cond in ('A1', 'A1.5'):
        raw = chat(msg(prompt_a1(problem, nodes, with_sigs=(cond == 'A1.5'))))
        return dict(parse_answer(raw, nodes), raw=raw, read=[])
    if cond == 'A2':
        raw1 = chat(msg(prompt_a2_read(problem, nodes)))
        mods = parse_read(raw1, nodes)
        contents = read_modules(nodes, mods)
        raw2 = chat(msg(prompt_a2_answer(problem, nodes, mods, contents)))
        return dict(parse_answer(raw2, nodes), raw=raw2, raw_read=raw1, read=mods)
    raise ValueError(cond)

def gold_sets(task):
    gf = {norm_id(x) for x in task['gold_functions']}
    gm = {norm_id(re.sub(r'\.py$', '', x).replace('/', '.')).replace('.__init__', '') for x in task['gold_files']}
    return gf, gm

def score(task, ans, decoy=None):
    gf, gm = gold_sets(task)
    rk = lambda lst, gold: next((i + 1 for i, x in enumerate(lst) if x in gold), None)
    r = dict(id=task['id'], repo=task['repo'], ok=ans['ok'], modules=ans['modules'], functions=ans['functions'],
             mod_rank=rk(ans['modules'], gm), fn_rank=rk(ans['functions'], gf), has_fn=bool(gf), read=ans.get('read', []))
    if decoy:
        dm = {norm_id(module_of_node(decoy))}
        r.update(decoy_fn_rank=rk(ans['functions'], {norm_id(decoy)}), decoy_mod_rank=rk(ans['modules'], dm))
    return r

def run(tasks, cond, graph_dir, problems, chat, overrides=None, decoys=None, workers=8, log=None):
    overrides = overrides or {}; decoys = decoys or {}
    def one(t):
        nodes = load_repo(f"{graph_dir}/{t['repo']}_{t['base_commit']}.json", overrides.get(t['id']))
        try: ans = localize(cond, problems[t['id']], nodes, chat)
        except Exception as e: ans = dict(ok=False, modules=[], functions=[], dropped=[], raw=f'ERROR {e}', read=[])
        out = score(t, ans, decoys.get(t['id'])); out['raw'] = ans.get('raw'); out['cond'] = cond
        return out
    with ThreadPoolExecutor(workers) as ex: rows = list(ex.map(one, tasks))
    if log: json.dump(rows, open(log, 'w'), indent=1)
    return rows

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - a) / d, (c + a) / d)

def summarize(rows, name=''):
    n = len(rows); fn = [r for r in rows if r['has_fn']]
    h = lambda xs, key, k: sum(1 for r in xs if r[key] and r[key] <= k)
    s = f"{name:5s} n={n} parsed={sum(r['ok'] for r in rows)}/{n} module@1={h(rows,'mod_rank',1)/n:.2f} module@3={h(rows,'mod_rank',3)/n:.2f} fn@1={h(fn,'fn_rank',1)/max(1,len(fn)):.2f} fn@5={h(fn,'fn_rank',5)/max(1,len(fn)):.2f}"
    lo, hi = wilson(h(rows, 'mod_rank', 3), n); s += f" (module@3 CI {lo:.2f}-{hi:.2f})"
    if rows and 'decoy_fn_rank' in rows[0]:
        s += f" | decoy fn@1={h(rows,'decoy_fn_rank',1)/n:.2f} fn@5={h(rows,'decoy_fn_rank',5)/n:.2f} module@3={h(rows,'decoy_mod_rank',3)/n:.2f}"
    return s
