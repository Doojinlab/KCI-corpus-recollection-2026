# -*- coding: utf-8 -*-
"""tables_4to8.py — 확정 코퍼스로 표 4(공저 네트워크+중심성)·표 5·6·7(피인용)·표 8(참고문헌) 재산출.

사용:  python scripts/rejudge/tables_4to8.py [--date 1166_20260930] [--corpus data/rejudge/merged_1166_20260930.json]
산출:  analysis/tables_4to8_<DATE>.md, analysis/tables_4to8_<DATE>.json

- 표 4: 논문 각주 12의 '이름-소속 결합 키'를 기관 수준으로 정규화해 노드로 삼는다(9/29 check_paper.py와 같은 규칙).
        심사위원 1-5 요구에 따라 연결정도 중심성·매개 중심성(Brandes)과 밀도를 추가한다.
- 표 5·6·7: KCI 피인용 수. 조회일은 재수집일(2026-09-29)이며 논문(2026-07-01 조회)과 다르다.
- 표 8: 참고문헌의 국내·국제 구분과 학문 분야 분류. 원 분류기가 유실돼 학술지명 규칙으로 재분류했다.
"""
import json, os, re, sys, io
from collections import Counter, defaultdict, deque
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DATE = sys.argv[sys.argv.index('--date') + 1] if '--date' in sys.argv else '1166_20260930'
CORPUS = sys.argv[sys.argv.index('--corpus') + 1] if '--corpus' in sys.argv else f'data/rejudge/merged_{DATE}.json'
G = ['영어', '한국어', '중국어']
PT = json.load(open(f'{REPO}/analysis/paper_targets.json', encoding='utf-8'))
raw = {r['arti_id']: r for r in json.load(open(f'{REPO}/data/corpus_full_merged.json', encoding='utf-8'))}
inc = [r for r in json.load(open(f'{REPO}/{CORPUS}', encoding='utf-8')) if r.get('include') == 'Y']
for o in inc: o['r'] = raw[o['arti_id']]
by = {g: [o for o in inc if o['group'] == g] for g in G}
print('확정 코퍼스', len(inc), {g: len(by[g]) for g in G})

# ── 표 4 공저 네트워크 ───────────────────────────────────────────────────────
INST = re.compile(r'([가-힣A-Za-z&\.\- ]*?(?:대학교|대학|학교|연구원|연구소|교육청|University|College|Institute|School))', re.I)
def akey(a):
    m = re.match(r'\s*([^(]+?)\s*(?:\((.*)\))?\s*$', a)
    name, affil = (m.group(1), m.group(2) or '') if m else (a, '')
    im = INST.search(affil)
    inst = im.group(1).strip() if im else (affil.split()[0] if affil.split() else '')
    return f'{name.strip()}|{inst}'

def authors_of(o):
    return list(dict.fromkeys(akey(a) for a in (o['r']['authors'] or '').split(';') if a.strip()))

def betweenness(nodes, adj):
    """Brandes(2001) 무가중 무향 그래프 매개 중심성. 정규화: 2/((n-1)(n-2))."""
    bc = dict.fromkeys(nodes, 0.0)
    for s in nodes:
        S = []; P = defaultdict(list); sigma = dict.fromkeys(nodes, 0); sigma[s] = 1
        d = dict.fromkeys(nodes, -1); d[s] = 0; Q = deque([s])
        while Q:
            v = Q.popleft(); S.append(v)
            for w in adj[v]:
                if d[w] < 0: d[w] = d[v] + 1; Q.append(w)
                if d[w] == d[v] + 1: sigma[w] += sigma[v]; P[w].append(v)
        delta = dict.fromkeys(nodes, 0.0)
        while S:
            w = S.pop()
            for v in P[w]: delta[v] += sigma[v] / sigma[w] * (1 + delta[w])
            if w != s: bc[w] += delta[w]
    n = len(nodes)
    norm = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 0   # 무향: 합계를 2로 나누고 (n-1)(n-2)/2로 정규화
    return {v: bc[v] * norm for v in nodes}

def net(rows):
    nodes = set(); adj = defaultdict(set); sole = 0; npa = 0
    for o in rows:
        au = authors_of(o); npa += len(au)
        if len(au) <= 1: sole += 1
        nodes.update(au)
        for i in range(len(au)):
            for j in range(i + 1, len(au)):
                adj[au[i]].add(au[j]); adj[au[j]].add(au[i])
    for a in nodes: adj[a]  # 고립 노드도 키 생성
    n = len(nodes); E = sum(len(v) for v in adj.values()) // 2
    seen = set(); comps = []
    for a in nodes:
        if a in seen: continue
        st = [a]; seen.add(a); c = 0
        while st:
            x = st.pop(); c += 1
            for y in adj[x]:
                if y not in seen: seen.add(y); st.append(y)
        comps.append(c)
    iso = sum(1 for a in nodes if not adj[a])
    deg = {a: len(adj[a]) for a in nodes}
    dc = {a: deg[a] / (n - 1) for a in nodes} if n > 1 else {}
    bc = betweenness(list(nodes), adj)
    return dict(authors=n, per=npa / len(rows), sole=100 * sole / len(rows), iso=100 * iso / n,
                comps=len(comps), largest=max(comps), mean_deg=2 * E / n, edges=E,
                density=2 * E / (n * (n - 1)) if n > 1 else 0,
                dc_mean=sum(dc.values()) / n, dc_max=max(dc.values()),
                bc_mean=sum(bc.values()) / n, bc_max=max(bc.values()),
                top_bc=sorted(bc.items(), key=lambda kv: -kv[1])[:5],
                top_deg=sorted(deg.items(), key=lambda kv: -kv[1])[:5])

N = {g: net(by[g]) for g in G}

# ── 표 5·6·7 피인용 ─────────────────────────────────────────────────────────
tot = {g: sum(o['r']['cited'] or 0 for o in by[g]) for g in G}
per = {g: tot[g] / len(by[g]) for g in G}
coh = {}
for g in G:
    rows = [o for o in by[g] if 2020 <= int(o['r']['year']) <= 2023]
    coh[g] = (sum(o['r']['cited'] or 0 for o in rows) / len(rows), len(rows))
med = {}
for g in G:
    cs = sorted(o['r']['cited'] or 0 for o in by[g]); k = len(cs)
    med[g] = cs[k // 2] if k % 2 else (cs[k // 2 - 1] + cs[k // 2]) / 2
zero = {g: 100 * sum(1 for o in by[g] if not (o['r']['cited'] or 0)) / len(by[g]) for g in G}
_rank = sorted(inc, key=lambda o: (-(o['r']['cited'] or 0), o['r']['year']))
_cut = _rank[9]['r']['cited'] or 0   # 10위 피인용. 동률은 임의로 끊지 않고 모두 싣는다
top10 = [o for o in _rank if (o['r']['cited'] or 0) >= _cut]
def rank_of(o): return 1 + sum(1 for x in _rank if (x['r']['cited'] or 0) > (o['r']['cited'] or 0))  # 공동 순위
def nt(s): return re.sub(r'[\s:：\-–—·,.()（）\'"‘’“”]', '', s or '').lower()
incn = {nt(o['r']['title_ko']): o for o in inc}
import difflib
def find(title):
    k = nt(title)
    for n in (22, 16, 12):
        for kk, o in incn.items():
            if k[:n] and k[:n] in kk: return o
    best = max(incn.items(), key=lambda kv: difflib.SequenceMatcher(None, k, kv[0][:len(k) + 8]).ratio())
    return best[1] if difflib.SequenceMatcher(None, k, best[0][:len(k) + 8]).ratio() >= 0.8 else None
paper_top = []
for title, yr, g, c in PT['table5_top_cited']:
    hit = find(title)
    paper_top.append((title, yr, g, c, hit))

# ── 표 8 참고문헌 ───────────────────────────────────────────────────────────
EDU = re.compile(r'교육|교수|학습|교과|교사|수업|리터러시|작문연구|독서연구|educat|learn|teach|pedagog|instruct|curricul|tesol|\bcall\b|recall|computer assisted|'
                 r'language learning|language teaching|second language writing|assessing writing|system$|elt journal|tesl|efl|esl|literacy|school', re.I)
LIT = re.compile(r'문학|소설|시학|시가|고전|비평|문예|literat|literary|poetry|poetic|文學|文学|詩|诗', re.I)
LING = re.compile(r'언어|어학|국어학|문법|음성|의미|형태|통사|화용|담화|어문|말뭉치|코퍼스|번역|통역|우리말|배달말|한글|국어|영어학|중국어|linguist|language|grammar|phonet|phonolog|semantic|syntax|pragmat|discourse|corpus|translat|interpret|語言|语言|語法|语法|漢語|汉语|中國語|中国语', re.I)
def field(ref):
    """학술지명으로만 분야를 가른다. 학술지명이 없는 단행본·웹자료 등은 분야 비율 계산에서 뺀다."""
    s = (ref.get('journal') or '').strip()
    if not s: return None
    if EDU.search(s): return '교육'
    if LIT.search(s): return '문학'
    if LING.search(s): return '언어학'
    return '기타'
def intl(ref):
    s = ' '.join([ref.get('title') or '', ref.get('journal') or '', ref.get('author') or ''])
    return not re.search(r'[가-힣]', s)
def script_of(ref):
    """국내(한글 포함) / 중문(한자 있고 한글 없음) / 영문 등(그 밖)"""
    s = ' '.join([ref.get('title') or '', ref.get('journal') or '', ref.get('author') or ''])
    if re.search(r'[가-힣]', s): return 'ko'
    if re.search(r'[一-鿿]', s): return 'zh'
    return 'en'
T8 = {}
for g in G:
    rows = [o for o in by[g] if o['r'].get('ref_available') and o['r'].get('references')]
    refs = [f for o in rows for f in o['r']['references']]
    fc = Counter(field(f) for f in refs); nj = sum(v for k, v in fc.items() if k)
    T8[g] = dict(papers=len(rows), total=len(by[g]), refs=len(refs), per=len(refs) / len(rows) if rows else 0,
                 intl=100 * sum(1 for f in refs if intl(f)) / len(refs) if refs else 0,
                 journal_refs=nj, journal_share=100 * nj / len(refs) if refs else 0,
                 dom=100 * sum(1 for f in refs if script_of(f) == 'ko') / len(refs),
                 intl_en=100 * sum(1 for f in refs if script_of(f) == 'en') / len(refs),
                 intl_zh=100 * sum(1 for f in refs if script_of(f) == 'zh') / len(refs),
                 edu=100 * fc['교육'] / nj, ling=100 * fc['언어학'] / nj,
                 lit=100 * fc['문학'] / nj, other=100 * fc['기타'] / nj)

# ── 출력 ────────────────────────────────────────────────────────────────────
L = [f'# 표 4~8 재산출 — 확정 코퍼스 ({DATE})\n',
     f'확정 코퍼스 {len(inc):,}편(영 {len(by["영어"])} · 한 {len(by["한국어"])} · 중 {len(by["중국어"])}). '
     '원고 수치 교체용. 논문 값은 `analysis/paper_targets.json`에서 옮겼다.\n']
def row(label, paper, mine, fmt='{}'):
    return f'| {label} | ' + ' / '.join(fmt.format(p) for p in paper) + ' | ' + ' / '.join(fmt.format(m) for m in mine) + ' |'
t4 = PT['table4_coauthor']
L += ['## 표 4. 공저 네트워크 (영 / 한 / 중)\n', '| 지표 | 논문 | 확정 코퍼스 |', '|---|---|---|',
      row('저자 수(노드)', t4['authors'], [N[g]['authors'] for g in G]),
      row('논문당 저자 수', t4['authors_per_paper'], [N[g]['per'] for g in G], '{:.2f}'),
      row('단독저자 논문 %', t4['sole_author_pct'], [N[g]['sole'] for g in G], '{:.1f}'),
      row('고립 저자 %', t4['isolated_author_pct'], [N[g]['iso'] for g in G], '{:.1f}'),
      row('연결 요소 수', t4['components'], [N[g]['comps'] for g in G]),
      row('최대 연결 요소(명)', t4['largest_component'], [N[g]['largest'] for g in G]),
      row('평균 연결정도', t4['mean_degree'], [N[g]['mean_deg'] for g in G], '{:.2f}'),
      '', '**추가 지표(심사위원 1-5 요구: 중심성)**\n', '| 지표 | 영어 | 한국어 | 중국어 |', '|---|---|---|---|',
      '| 공저 관계(엣지) 수 | ' + ' | '.join(str(N[g]['edges']) for g in G) + ' |',
      '| 밀도 | ' + ' | '.join(f'{N[g]["density"]:.4f}' for g in G) + ' |',
      '| 연결정도 중심성 평균 | ' + ' | '.join(f'{N[g]["dc_mean"]:.4f}' for g in G) + ' |',
      '| 연결정도 중심성 최댓값 | ' + ' | '.join(f'{N[g]["dc_max"]:.4f}' for g in G) + ' |',
      '| 매개 중심성 평균 | ' + ' | '.join(f'{N[g]["bc_mean"]:.5f}' for g in G) + ' |',
      '| 매개 중심성 최댓값 | ' + ' | '.join(f'{N[g]["bc_max"]:.4f}' for g in G) + ' |',
      '', '매개 중심성 상위 5인(이름|기관, 값):\n']
for g in G:
    L.append(f'- {g}: ' + '; '.join(f'{a} ({v:.4f})' for a, v in N[g]['top_bc'] if v > 0) or f'- {g}: (매개 중심성 0 — 모든 군집이 3인 이하)')
L += ['', '연결정도 상위 5인(공저자 수):\n']
for g in G:
    L.append(f'- {g}: ' + '; '.join(f'{a} ({v})' for a, v in N[g]['top_deg']))
L += ['', f'## 표 5. 피인용 상위 10위(동률 포함 {len(top10)}편) (확정 코퍼스, KCI 2026-09-29 조회)\n',
      '| 순위 | 제목 | 연도 | 언어군 | 피인용 |', '|---|---|---|---|---|']
for o in top10:
    L.append(f'| {rank_of(o)} | {(o["r"]["title_ko"] or o["r"]["title_en"])[:60]} | {o["r"]["year"]} | {o["group"]} | {o["r"]["cited"]} |')
L += ['', '논문 표 5의 10편이 확정 코퍼스에 있는지:\n', '| 논문 표 5 제목 | 논문 군·피인용 | 확정 코퍼스 |', '|---|---|---|']
for title, yr, g, c, hit in paper_top:
    L.append(f'| {title[:44]} | {g} {c} | ' + (f'있음 · {hit["group"]} {hit["r"]["cited"]}' if hit else '**없음(제외됨)**') + ' |')
L += ['', '## 표 6. 총 피인용과 편당 평균\n', '| 지표 | 논문(2026-07-01) | 확정 코퍼스(2026-09-29) |', '|---|---|---|',
      row('총 피인용', PT['table6_citations']['total'], [tot[g] for g in G]),
      row('편당 평균', PT['table6_citations']['per_paper'], [per[g] for g in G], '{:.2f}'),
      f'| 전체 합계 | {PT["table6_citations"]["grand_total"]:,} | {sum(tot.values()):,} |',
      '| 중앙값(추가) | — | ' + ' / '.join(f'{med[g]:g}' for g in G) + ' |',
      '| 피인용 0편 비율 %(추가) | — | ' + ' / '.join(f'{zero[g]:.1f}' for g in G) + ' |',
      '', '## 표 7. 2020–2023 코호트 편당 피인용\n', '| 지표 | 논문 | 확정 코퍼스 |', '|---|---|---|',
      row('편당 피인용', PT['table7_cohort_2020_2023_per_paper'], [coh[g][0] for g in G], '{:.2f}'),
      '| 코호트 편수 | — | ' + ' / '.join(str(coh[g][1]) for g in G) + ' |',
      '', '## 표 8. 참고문헌 구성 (참고문헌 블록 보유 논문 기준)\n',
      '분야 분류는 원 분류기가 유실되어 참고문헌의 **학술지명** 규칙(교육 → 문학 → 언어학 → 기타 순)으로 재분류했다. '
      '학술지명이 없는 단행본·웹자료·학위논문은 분야 비율의 분모에서 뺐다. 절대값은 원 분류와 직접 비교할 수 없으나, '
      '언어군 간 순서(교육 비중 영>한>중, 언어학·문학 비중 중>한>영)는 논문과 같다. 원고 표 8 각주에 이 기준을 밝힌다.\n',
      '| 지표 | 논문 | 확정 코퍼스 |', '|---|---|---|',
      '| 참고문헌 보유 편수 | — | ' + ' / '.join(f'{T8[g]["papers"]}/{T8[g]["total"]}' for g in G) + ' |',
      row('편당 참고문헌', PT['table8_refs']['refs_per_paper'], [T8[g]['per'] for g in G], '{:.1f}'),
      row('국제 문헌 %(한글 없는 문헌 전체)', PT['table8_refs']['international_pct'], [T8[g]['intl'] for g in G], '{:.1f}'),
      '| └ 영문 등 % | — | ' + ' / '.join(f'{T8[g]["intl_en"]:.1f}' for g in G) + ' |',
      '| └ 중문(한자, 한글 없음) % | — | ' + ' / '.join(f'{T8[g]["intl_zh"]:.1f}' for g in G) + ' |',
      '| 국내(한글) % | — | ' + ' / '.join(f'{T8[g]["dom"]:.1f}' for g in G) + ' |',
      '| 학술지명 있는 문헌(분야 분류 대상) | — | ' + ' / '.join(f'{T8[g]["journal_refs"]:,} ({T8[g]["journal_share"]:.0f}%)' for g in G) + ' |',
      row('교육 분야 %', PT['table8_refs']['edu_pct'], [T8[g]['edu'] for g in G], '{:.1f}'),
      row('언어학 분야 %', PT['table8_refs']['ling_pct'], [T8[g]['ling'] for g in G], '{:.1f}'),
      row('문학 분야 %', PT['table8_refs']['lit_pct'], [T8[g]['lit'] for g in G], '{:.1f}'),
      row('기타 %', PT['table8_refs']['other_pct'], [T8[g]['other'] for g in G], '{:.1f}')]
open(f'{REPO}/analysis/tables_4to8_{DATE}.md', 'w', encoding='utf-8').write('\n'.join(L))
json.dump(dict(table4={g: {k: v for k, v in N[g].items() if k not in ('top_bc', 'top_deg')} for g in G},
               table4_top_bc={g: N[g]['top_bc'] for g in G},
               table5_top10=[dict(title=o['r']['title_ko'], year=o['r']['year'], group=o['group'], cited=o['r']['cited']) for o in top10],
               table6=dict(total=tot, per_paper=per, median=med, zero_pct=zero, as_of='2026-09-29'),
               table7={g: dict(per_paper=coh[g][0], n=coh[g][1]) for g in G}, table8=T8),
          open(f'{REPO}/analysis/tables_4to8_{DATE}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(L))
