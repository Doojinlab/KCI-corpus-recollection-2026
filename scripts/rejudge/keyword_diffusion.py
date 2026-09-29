# -*- coding: utf-8 -*-
"""keyword_diffusion.py — 확정 코퍼스로 표 3·그림 4(주제 확산 시차)와 4.3 공유 키워드 수를 재산출.

사용:  python scripts/rejudge/keyword_diffusion.py [--date 20260930] [--corpus data/rejudge/merged_20260930.json]
전제:  analysis/keyword_concepts.json (20개 핵심 개념 정규화표)
산출:  analysis/keyword_diffusion_YYYYMMDD.md
       analysis/keyword_diffusion_YYYYMMDD.json (개념×언어군 최초 출현연도·편수)

논문 각주 11의 경고를 그대로 반영한다: '최초 출현연도'는 표본이 클수록 이른 해가 관측되는 극단
순서통계량이므로, 규모를 맞춘 비교(언어군별 동일 편수 무작위 축소 반복)를 함께 제시한다.
"""
import json, os, sys, re, random, statistics as st
from collections import Counter, defaultdict

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DATE = sys.argv[sys.argv.index('--date') + 1] if '--date' in sys.argv else '20260930'
CORPUS = sys.argv[sys.argv.index('--corpus') + 1] if '--corpus' in sys.argv else f'data/rejudge/merged_{DATE}.json'
GROUPS = ['영어', '한국어', '중국어']
B = 2000  # 규모 맞춤 반복 횟수

CT = json.load(open(f'{REPO}/analysis/keyword_concepts.json', encoding='utf-8'))
CONCEPTS = sorted(CT['concepts'], key=lambda c: c['priority'])
for c in CONCEPTS:
    c['re'] = re.compile('|'.join(c['patterns']), re.I)
MODULES = CT['modules']

def norm_kw(s):
    s = re.sub(r'\s+', ' ', (s or '')).strip().lower()
    return re.sub(r'[·\-–—]+', ' ', s).strip()

def concepts_of(kw):
    """키워드 하나 → 개념 id(없으면 None)"""
    for c in CONCEPTS:
        if c['re'].search(kw): return c['id']
    return None

def keywords_of(rec):
    out = []
    for f in ('kw_ko', 'kw_en'):
        for k in re.split(r'[;,]', rec.get(f) or ''):
            k = norm_kw(k)
            if len(k) > 1: out.append(k)
    return out

def main():
    rows = [r for r in json.load(open(f'{REPO}/{CORPUS}', encoding='utf-8')) if r.get('include') == 'Y']
    print(f'확정 코퍼스 {len(rows)}편', dict(Counter(r["group"] for r in rows)))
    # 논문별 개념/정규화 키워드 집합
    per = []
    for r in rows:
        kws = keywords_of(r)
        cs = {c for c in (concepts_of(k) for k in kws) if c}
        # 논문 4.3·각주 10의 방법: 20개 개념에 걸리는 키워드는 개념 id로 동의어 통합, 나머지는 소문자·공백 정규화만
        norm = {concepts_of(k) or k for k in kws}
        per.append(dict(group=r['group'], year=int(r['year']), concepts=cs, kws=norm))
    # 1) 개념별 언어군 최초 출현연도·편수
    first = {c['id']: {} for c in CONCEPTS}
    cnt = {c['id']: Counter() for c in CONCEPTS}
    for p in per:
        for cid in p['concepts']:
            cnt[cid][p['group']] += 1
            if p['group'] not in first[cid] or p['year'] < first[cid][p['group']]:
                first[cid][p['group']] = p['year']
    # 2) 모듈별 최초 출현연도(구성 개념 최소값)
    mod_first = {}
    for m in MODULES:
        mod_first[m['name']] = {}
        for g in GROUPS:
            ys = [first[cid][g] for cid in m['concepts'] if g in first[cid]]
            if ys: mod_first[m['name']][g] = min(ys)
    # 3) 공유 키워드 수 (개념 통합 + 정규화 키워드 기준, 논문 4.3)
    kwg = {g: set() for g in GROUPS}
    for p in per: kwg[p['group']] |= p['kws']
    cg = {g: set() for g in GROUPS}
    for p in per: cg[p['group']] |= p['concepts']
    shared = {
        'all3': len(kwg['영어'] & kwg['한국어'] & kwg['중국어']),
        'en_ko': len(kwg['영어'] & kwg['한국어']),
        'en_zh': len(kwg['영어'] & kwg['중국어']),
        'ko_zh': len(kwg['한국어'] & kwg['중국어']),
    }
    # 4) 공유 키워드 최초 출현 시차 중앙값
    kwfirst = {g: {} for g in GROUPS}
    for p in per:
        for k in p['kws']:
            if k not in kwfirst[p['group']] or p['year'] < kwfirst[p['group']][k]:
                kwfirst[p['group']][k] = p['year']
    def lag(a, b):
        ks = set(kwfirst[a]) & set(kwfirst[b])
        d = [kwfirst[b][k] - kwfirst[a][k] for k in ks]
        return (st.median(d) if d else None), len(d)
    lags = {'영어→한국어': lag('영어', '한국어'), '영어→중국어': lag('영어', '중국어'), '한국어→중국어': lag('한국어', '중국어')}
    # 5) 규모 맞춤: 영·한군을 중국어군 편수로 무작위 축소해 모듈 최초 출현연도 분포
    nzh = sum(1 for p in per if p['group'] == '중국어')
    rnd = random.Random(20260930)
    size_matched = {}
    for m in MODULES:
        size_matched[m['name']] = {}
        for g in ('영어', '한국어'):
            pool = [p for p in per if p['group'] == g]
            ys = []
            for _ in range(B):
                s = rnd.sample(pool, min(nzh, len(pool)))
                yy = [p['year'] for p in s if p['concepts'] & set(m['concepts'])]
                if yy: ys.append(min(yy))
            if ys:
                ys.sort()
                size_matched[m['name']][g] = dict(median=st.median(ys), p05=ys[int(0.05 * len(ys))], p95=ys[int(0.95 * len(ys)) - 1], n=len(ys))
    out = dict(corpus=CORPUS, n=len(rows), n_by_group=dict(Counter(r['group'] for r in rows)),
               concept_first_year={cid: first[cid] for cid in first}, concept_counts={cid: dict(cnt[cid]) for cid in cnt},
               module_first_year=mod_first, shared_keywords=shared, shared_concepts={g: len(cg[g]) for g in GROUPS},
               leadlag=lags, size_matched=size_matched, n_zh=nzh)
    json.dump(out, open(f'{REPO}/analysis/keyword_diffusion_{DATE}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    PT = json.load(open(f'{REPO}/analysis/paper_targets.json', encoding='utf-8'))
    L = [f'# 주제 확산·시차 재산출 ({DATE})\n',
         f'확정 코퍼스 {len(rows)}편(영 {out["n_by_group"].get("영어",0)}·한 {out["n_by_group"].get("한국어",0)}·중 {out["n_by_group"].get("중국어",0)}).',
         '정규화표: `analysis/keyword_concepts.json`(20개 핵심 개념). 논문 3.3(3)·4.3·표 3·그림 4 대응.\n',
         '## 1. 개념별 최초 출현연도와 편수\n',
         '| 개념 | 영어 최초(편수) | 한국어 최초(편수) | 중국어 최초(편수) |\n|---|---|---|---|']
    for c in CONCEPTS:
        cells = []
        for g in GROUPS:
            y = first[c['id']].get(g); n = cnt[c['id']][g]
            cells.append(f'{y} ({n})' if y else '— (0)')
        L.append(f'| {c["name"]} | ' + ' | '.join(cells) + ' |')
    L.append('\n## 2. 표 3 재산출 — 주제군별 최초 출현과 영→중 시차\n')
    L.append('| 주제군 | 영어 | 한국어 | 중국어 | 영→중 시차 | 논문 보고(영/한/중) |\n|---|---|---|---|---|---|')
    for m in MODULES:
        f_ = mod_first[m['name']]
        gap = (f_['중국어'] - f_['영어']) if ('중국어' in f_ and '영어' in f_) else None
        pt = PT['table3_first_year'].get(m['name'].split('(')[0].strip()) or PT['table3_first_year'].get(m['name'])
        L.append(f'| {m["name"]} | {f_.get("영어","—")} | {f_.get("한국어","—")} | {f_.get("중국어","—")} | ' +
                 (f'{gap}년' if gap is not None else '—') + ' | ' + ('/'.join(map(str, pt)) if pt else '—') + ' |')
    L.append('\n## 3. 규모를 맞춘 최초 출현연도 (심사위원 2 지적·논문 각주 11)\n')
    L.append(f'영·한군에서 중국어군과 같은 {nzh}편을 무작위로 뽑아 최초 출현연도를 {B}회 재계산한 분포. '
             '중국어군 실측값이 이 구간 안에 들면 "늦게 출현했다"는 진술은 규모 효과로 설명된다.\n')
    L.append('| 주제군 | 중국어 실측 | 영어 축소 중앙값(5–95%) | 한국어 축소 중앙값(5–95%) | 판정 |\n|---|---|---|---|---|')
    for m in MODULES:
        zh = mod_first[m['name']].get('중국어'); sm = size_matched[m['name']]
        def fmt(g):
            d = sm.get(g)
            return f'{d["median"]:.0f} ({d["p05"]}–{d["p95"]})' if d else '—'
        verdict = '—'
        if zh and sm.get('영어'):
            verdict = '규모 효과로 설명 가능' if zh <= sm['영어']['p95'] else '규모로 설명 안 됨(실질 지연)'
        L.append(f'| {m["name"]} | {zh or "—"} | {fmt("영어")} | {fmt("한국어")} | {verdict} |')
    L.append('\n## 4. 공유 키워드 수와 시차 (4.3)\n')
    L.append('| 항목 | 재산출 | 논문 |\n|---|---|---|')
    L.append(f'| 세 군 공유 | {shared["all3"]} | {PT["shared_keywords"]["all3"]} |')
    L.append(f'| 영–한 공유 | {shared["en_ko"]} | {PT["shared_keywords"]["en_ko"]} |')
    L.append(f'| 영–중 공유 | {shared["en_zh"]} | {PT["shared_keywords"]["en_zh"]} |')
    L.append(f'| 한–중 공유 | {shared["ko_zh"]} | {PT["shared_keywords"]["ko_zh"]} |')
    L.append('')
    L.append('| 시차(공유 키워드 최초 출현 차의 중앙값) | 재산출 | 공유 키워드 수 | 논문 |\n|---|---|---|---|')
    for k, pk in (('영어→한국어', 'en_to_ko'), ('영어→중국어', 'en_to_zh'), ('한국어→중국어', 'ko_to_zh')):
        med, n = lags[k]
        L.append(f'| {k} | ' + (f'{med:+.1f}년' if med is not None else '—') + f' | {n} | {PT["leadlag_median_years"][pk]:+.1f}년 |')
    L.append('\n개념 단위로는 언어군별 보유 개념 수: ' + ', '.join(f'{g} {out["shared_concepts"][g]}/20' for g in GROUPS) + '.')
    L.append('\n## 5. 원고 반영 지침\n')
    L.append('- 표 3은 위 2절 값으로 교체하고, 3절 표를 부록 또는 각주 11 확장으로 함께 싣는다.')
    L.append('- 규모 축소 구간에 중국어 실측값이 들어가는 주제군은 "늦게 출현"이라는 서술을 "소규모 코퍼스에서 기대되는 범위"로 고친다.')
    L.append('- 4.3의 공유 키워드 수·시차는 4절 값으로 교체하고, 정규화표를 부록에 수록한다(파일: analysis/keyword_concepts.json).')
    open(f'{REPO}/analysis/keyword_diffusion_{DATE}.md', 'w', encoding='utf-8').write('\n'.join(L))
    print('saved analysis/keyword_diffusion_%s.md' % DATE)
    print('\n'.join(L[:12]))

if __name__ == '__main__':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
