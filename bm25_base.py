import json, math, re, sys, os
from collections import Counter
TASKS='/mnt/user-data/attachments/687e76e1-241e-57c5-afc2-47566b535e1c/92233abb-tasks.jsonl'
SET=sys.argv[1] if len(sys.argv)>1 else 'task_set_40.json'
GRAPHS=sys.argv[2] if len(sys.argv)>2 else '/mnt/user-data/uploads/gemma-4-developer-agent/graphs'
OUT=sys.argv[3] if len(sys.argv)>3 else 'bm25_results.json'
def is_test(nid):
    p=nid.split('.')
    return 'tests' in p or 'test' in p or any(x.startswith('test_') for x in p[:-1]) or 'docs_src' in p or 'scripts' in p or 'conftest' in p
def norm_id(n): return n[4:] if n.startswith('src.') else n
def file_of(nid):
    p=norm_id(nid).split('.')
    for i,c in enumerate(p):
        if i>0 and c[:1].isupper(): return '.'.join(p[:i])
    return '.'.join(p[:-1]) if len(p)>1 else nid
def tok(s):
    s=re.sub(r'([a-z0-9])([A-Z])',r'\1 \2',s)
    return [w for w in re.findall(r'[a-z0-9]+',s.lower()) if len(w)>1]
class BM25:
    def __init__(s,docs,k1=1.2,b=0.75):
        s.docs=[Counter(d) for d in docs]; s.len=[len(d) for d in docs]; s.avg=sum(s.len)/max(1,len(docs)); s.k1=k1; s.b=b
        df=Counter(); [df.update(d.keys()) for d in s.docs]; N=len(docs)
        s.idf={w:math.log(1+(N-n+.5)/(n+.5)) for w,n in df.items()}
    def score(s,q):
        q=Counter(q); out=[]
        for d,l in zip(s.docs,s.len):
            sc=0
            for w in q:
                f=d.get(w,0)
                if f: sc+=s.idf[w]*f*(s.k1+1)/(f+s.k1*(1-s.b+s.b*l/s.avg))
            out.append(sc)
        return out
def wilson(k,n,z=1.96):
    if n==0: return (0,0)
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); a=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return ((c-a)/d,(c+a)/d)
probs={}
for l in open(TASKS):
    d=json.loads(l); probs[d['instance_id']]=d['problem_statement']
tasks=json.load(open(SET)); Ks=[1,3,5,10]
res={}
for variant in ('B1','B2'):
    rows=[]
    for t in tasks:
        g=json.load(open(f"{GRAPHS}/{t['repo']}_{t['base_commit']}.json"))
        nodes=[n for n in g['nodes'] if not is_test(n['id'])]
        if variant=='B1': docs=[tok(n['id']) for n in nodes]
        else: docs=[tok(n['id'])*3+tok(n.get('text','')) for n in nodes]
        bm=BM25(docs); q=tok(probs[t['id']][:6000]); sc=bm.score(q)
        order=sorted(range(len(nodes)),key=lambda i:-sc[i])
        ranked=[nodes[i]['id'] for i in order]
        gf={norm_id(x) for x in t['gold_functions']}
        gfile={norm_id(re.sub(r'\.py$','',x).replace('/','.')) .replace('.__init__','') for x in t['gold_files']}
        # function rank
        fr=next((i+1 for i,n in enumerate(ranked) if norm_id(n) in gf),None)
        # file rank over distinct files
        seen=[];[seen.append(file_of(n)) for n in ranked if file_of(n) not in seen]
        flr=next((i+1 for i,f in enumerate(seen) if f in gfile),None)
        rows.append(dict(id=t['id'],repo=t['repo'],has_fn=bool(gf),fn_rank=fr,file_rank=flr,top10=ranked[:10],n_nodes=len(nodes)))
    res[variant]=rows
json.dump(res,open(OUT,'w'),indent=1)
for v,rows in res.items():
    print('=====',v)
    for scope,sel in (('all',rows),('fastapi',[r for r in rows if r['repo']=='fastapi']),('rich',[r for r in rows if r['repo']=='rich']),('requests',[r for r in rows if r['repo']=='requests'])):
        fn=[r for r in sel if r['has_fn']]
        s=f"{scope:9s} n={len(sel):2d} file@"+' '.join(f"{k}={sum(1 for r in sel if r['file_rank'] and r['file_rank']<=k)/max(1,len(sel)):.2f}" for k in Ks)
        s+=f" | fn(n={len(fn)}) @"+' '.join(f"{k}={sum(1 for r in fn if r['fn_rank'] and r['fn_rank']<=k)/max(1,len(fn)):.2f}" for k in Ks)
        print(s)
    k=5; a=[r for r in rows if r['file_rank'] and r['file_rank']<=k]; lo,hi=wilson(len(a),len(rows)); print(f"file@5 95% CI {lo:.2f} to {hi:.2f}")
    print('missing file rank',[r['id'] for r in rows if r['file_rank'] is None][:12])
