"""Published Tuesday 21:00 emergency times against the curve values at 20:00
and 22:00 (26 October 2026): neighbourhoods and cells outside the interval,
on which side, by how many minutes, and the mean times at 20:00, 21:00 and
22:00. Run from the project root:
python scripts/analysis/curve_21h_gaps.py
"""
import json, glob, numpy as np, pandas as pd
cur = json.load(open('data/processed/routes_curve_v2.json'))
blocks = cur['layout']['blocks']
def pub(slot, prof):
    d = json.load(open(f'data/processed/routes_iris_{slot}.json'))
    b, t = d['layout']['blocks'], d['layout']['types']
    i = b.index(f'time:{prof}') * len(t) + t.index('emergency')
    return {k: v[i] for k, v in d['iris'].items()}
inh = [k for k in cur['iris']]
for prof, off in (('standard', 0), ('step_free_no', 12)):
    p21 = pub('tue21', prof)
    rows = []
    for k, v in cur['iris'].items():
        a, b, x = v[off + 10], v[off + 11], p21.get(k)
        if None in (a, b, x): continue
        lo, hi = min(a, b), max(a, b)
        if x < lo: rows.append(('below', lo - x))
        elif x > hi: rows.append(('above', x - hi))
    df = pd.DataFrame(rows, columns=['side', 'gap'])
    print(prof, len(df), df.side.value_counts().to_dict(), 'gap distribution', df.gap.value_counts().sort_index().head(8).to_dict())
# cell level, wheelchair
def cells(path, name):
    fs = sorted(glob.glob(f'{path}/{name}_*.parquet'))
    t = pd.concat([pd.read_parquet(f) for f in fs]); t = t[t.type == 'emergency']
    return t.set_index('cell_id').minutes
for prof in ('standard', 'step_free_no'):
    c21 = cells('data/interim/access/routes_ttm_v2', f'{prof}_tue21')
    c20 = cells('data/interim/access/routes_ttm_curve_v2', f'{prof}_tue20')
    c22 = cells('data/interim/access/routes_ttm_curve_v2', f'{prof}_tue22')
    df = pd.concat([c20.rename('a'), c21.rename('x'), c22.rename('b')], axis=1).dropna()
    lo, hi = df[['a', 'b']].min(axis=1), df[['a', 'b']].max(axis=1)
    out = (df.x < lo) | (df.x > hi)
    print(prof, 'cells', len(df), 'outside', round(100 * out.mean(), 1), '% ; above', round(100 * (df.x > hi).mean(), 1), '% below', round(100 * (df.x < lo).mean(), 1), '% ; median gap when above', (df.x - hi)[df.x > hi].median())
    print('   mean minutes 20h/21h/22h', df.a.mean().round(1), df.x.mean().round(1), df.b.mean().round(1))
