# -*- coding: utf-8 -*-
"""check_paper.py — 재구성 코퍼스(reconstructed_1142.json)를 논문 보고값(analysis/paper_targets.json)과 전 항목 대조."""
import json, os, re, sys
from collections import Counter, defaultdict
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
T = json.load(open(f'{REPO}/analysis/paper_targets.json', encoding='utf-8'))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'reconstructed_1142.json'
rec = json.load(open(f'{REPO}/data/{SRC}', encoding='utf-8'))
raw = {r['arti_id']: r for r in json.load(open(f'{REPO}/data/corpus_full_merged.json', encoding='utf-8'))}
G = ['영어', '한국어', '중국어']
for o in rec: o['r'] = raw[o['arti_id']]
by = {g: [o for o in rec if o['group'] == g] for g in G}
out = []
def P(*a): out.append(' '.join(str(x) for x in a))
def row3(label, paper, mine, fmt='{}'):
    d = ['' if p == '' else (mine[i] - p if isinstance(p, (int, float)) else '') for i, p in enumerate(paper)]
    P(f'{label:<22}| 논문 {" / ".join(fmt.format(p) for p in paper):<24}| 재구성 {" / ".join(fmt.format(m) for m in mine):<24}| 차 {" / ".join(("%+.2f" % x if isinstance(x, float) else "%+d" % x) if x != "" else "-" for x in d)}')

# ── 1. 연도 ──
P('=== 그림 2 연도별 편수 ===')
yt = Counter(o['r']['year'] for o in rec); yz = Counter(o['r']['year'] for o in by['중국어']); ye = Counter(o['r']['year'] for o in by['영어'])
for y in range(2020, 2027):
    P(f'{y}: 논문 {T["year_total"][str(y)]:>3} / 재구성 {yt[y]:>3} ({yt[y]-T["year_total"][str(y)]:+d}) | 중국어 논문 {T["year_zh"].get(str(y), "≤2"):>3} / 재구성 {yz[y]:>2} | 영어 비중 {100*ye[y]/yt[y]:.0f}% (논문 54–82%)')

# ── 2. 표 2 연구방법(전체 1,142) ──
P('\n=== 표 2 연구방법 분포 (전체) ===')
cm = {g: Counter(o['meth'] for o in by[g]) for g in G}
for m, p in T['table2_method'].items(): row3(m, p, [cm[g][m] for g in G])
exp = [100 * cm[g]['실험연구'] / len(by[g]) for g in G]; be = [100 * (cm[g]['개발연구'] + cm[g]['성능평가']) / len(by[g]) for g in G]
row3('그림3 실험 비중%', T['fig3_exp_share'], [round(x, 1) for x in exp], '{:.1f}')
row3('그림3 구축·평가형%', T['fig3_build_eval_share'], [round(x, 1) for x in be], '{:.1f}')

# ── 3. 표 10 기능 ──
P('\n=== 표 10 언어기능 분포 ===')
cf = {g: Counter(o['func'] for o in by[g]) for g in G}
for f, p in T['table10_function'].items(): row3(f, p, [cf[g][f] for g in G])

# ── 4. 표 11·12 격자 ──
P('\n=== 표 11 격자 점유율 ===')
FUN = [f for f in T['table10_function'] if f != '기능비특정']; MET = list(T['table2_method'])
grid = {g: Counter((o['func'], o['meth']) for o in by[g] if o['func'] != '기능비특정') for g in G}
filled = [sum(1 for f in FUN for m in MET if grid[g][(f, m)] > 0) for g in G]
npap = [sum(grid[g].values()) for g in G]
row3('격자 대상 논문', T['table11_occupancy']['grid_papers'], npap)
row3('채워진 칸', T['table11_occupancy']['filled_cells'], filled)
row3('충전율%', T['table11_occupancy']['fill_pct'], [round(100 * x / 88, 1) for x in filled], '{:.1f}')
row3('칸당 평균 편수', T['table11_occupancy']['per_cell'], [round(npap[i] / filled[i], 1) for i in range(3)], '{:.1f}')
P('\n=== 표 12 확산대기 상위 10 (영/한/중) ===')
for f, m, e, k, z in T['table12_diffusion_pending']:
    me, mk, mz = grid['영어'][(f, m)], grid['한국어'][(f, m)], grid['중국어'][(f, m)]
    P(f'{f}×{m:<8}| 논문 {e:>2}/{k:>2}/{z} | 재구성 {me:>2}/{mk:>2}/{mz} | 차 {me-e:+d}/{mk-k:+d}/{mz-z:+d}')
lead = {(f, m): grid['영어'][(f, m)] + grid['한국어'][(f, m)] for f in FUN for m in MET}
zh = {(f, m): grid['중국어'][(f, m)] for f in FUN for m in MET}
gap = [k for k in zh if zh[k] <= 1]; wait = [k for k in gap if lead[k] >= 10]; struct = [k for k in gap if lead[k] == 0 and zh[k] == 0]
P(f'공백(중≤1) {len(gap)} (논문 79) | 확산대기(선도군≥10) {len(wait)} (답변서 18) | 구조공백 {len(struct)} (논문 18) | 저축적 {len(gap)-len(wait)-len(struct)} (43)')
top = sorted([k for k in gap], key=lambda k: -lead[k])[:10]
P('재구성 확산대기 상위10:', ', '.join(f'{f}×{m}({lead[(f,m)]})' for f, m in top))
P('재구성 구조공백:', ', '.join(f'{f}×{m}' for f, m in struct))

# ── 5. 표 4 공저 네트워크 ──
P('\n=== 표 4 공저 네트워크 ===')
INST = re.compile(r'([가-힣A-Za-z&\.\- ]*?(?:대학교|대학|학교|연구원|연구소|교육청|University|College|Institute|School))', re.I)
def akey(a):
    """저자 노드 키: 이름 + 기관(학과·직위 제거). 논문 각주 12의 '이름-소속 결합 키'를 기관 수준으로 정규화."""
    m = re.match(r'\s*([^(]+?)\s*(?:\((.*)\))?\s*$', a)
    name, affil = (m.group(1), m.group(2) or '') if m else (a, '')
    im = INST.search(affil)
    inst = im.group(1).strip() if im else affil.split()[0] if affil.split() else ''
    return f'{name.strip()}|{inst}'
def net(rows):
    nodes = set(); deg = Counter(); adj = defaultdict(set); sole = 0
    for o in rows:
        au = list(dict.fromkeys(akey(a) for a in (o['r']['authors'] or '').split(';') if a.strip()))
        if len(au) <= 1: sole += 1
        for a in au: nodes.add(a)
        for i in range(len(au)):
            for j in range(i + 1, len(au)):
                if au[j] not in adj[au[i]]: adj[au[i]].add(au[j]); adj[au[j]].add(au[i])
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
    return dict(authors=n, per=sum(len((o['r']['authors'] or '').split(';')) for o in rows) / len(rows), sole=100 * sole / len(rows),
                iso=100 * iso / n, comps=len(comps), largest=max(comps), deg=2 * E / n)
N = {g: net(by[g]) for g in G}
t4 = T['table4_coauthor']
row3('저자 수', t4['authors'], [N[g]['authors'] for g in G])
row3('논문당 저자', t4['authors_per_paper'], [round(N[g]['per'], 2) for g in G], '{:.2f}')
row3('단독저자 %', t4['sole_author_pct'], [round(N[g]['sole'], 1) for g in G], '{:.1f}')
row3('고립 저자 %', t4['isolated_author_pct'], [round(N[g]['iso'], 1) for g in G], '{:.1f}')
row3('연결 요소', t4['components'], [N[g]['comps'] for g in G])
row3('최대 군집', t4['largest_component'], [N[g]['largest'] for g in G])
row3('평균 연결정도', t4['mean_degree'], [round(N[g]['deg'], 2) for g in G], '{:.2f}')

# ── 6. 표 5·6·7 인용 ──
P('\n=== 표 5 피인용 상위 10 (논문 제목 → 재구성 코퍼스 내 존재/군/피인용[2026-09-29]) ===')
import difflib
def norm(s): return re.sub(r'[\s:：\-–—·,.()（）]', '', s or '').lower()
allrec = {norm(o['r']['title_ko']): o for o in rec}
allraw = {norm(r['title_ko']): r for r in raw.values()}
def find(d, key):
    for n in (24, 18, 14):
        for k, o in d.items():
            if key[:n] in k: return o
    best = max(d.items(), key=lambda kv: difflib.SequenceMatcher(None, key, kv[0][:len(key) + 10]).ratio())
    return best[1] if difflib.SequenceMatcher(None, key, best[0][:len(key) + 10]).ratio() > 0.6 else None
for title, yr, g, c in T['table5_top_cited']:
    key = norm(title); hit = find(allrec, key)
    if hit: P(f'  O {title[:34]:<36} 논문 {g} {c} | 재구성 {hit["group"]} {hit["r"]["cited"]} {"" if hit["group"]==g else "★군 불일치"}')
    else:
        rr = find(allraw, key)
        P(f'  X {title[:34]:<36} 논문 {g} {c} | 코퍼스에 없음' + (f' (원본에는 있음: 시트 {rr["orig_group"]}, 제외됨)' if rr else ' (원본 1,644에도 없음)'))
top10 = sorted(rec, key=lambda o: -(o['r']['cited'] or 0))[:10]
P('재구성 상위10:', ' | '.join(f'{o["r"]["title_ko"][:18]}({o["group"][0]},{o["r"]["cited"]})' for o in top10))
P('\n=== 표 6·7 피인용 (논문 2026-07-01 조회, 재구성 2026-09-29 조회) ===')
tot = [sum(o['r']['cited'] or 0 for o in by[g]) for g in G]
row3('총 피인용', T['table6_citations']['total'], tot)
row3('편당 평균', T['table6_citations']['per_paper'], [round(tot[i] / len(by[g]), 2) for i, g in enumerate(G)], '{:.2f}')
P(f'전체 합 {sum(tot)} (논문 5,409)')
coh = []
for g in G:
    rows = [o for o in by[g] if 2020 <= o['r']['year'] <= 2023]
    coh.append(round(sum(o['r']['cited'] or 0 for o in rows) / len(rows), 2))
row3('2020–23 편당', T['table7_cohort_2020_2023_per_paper'], coh, '{:.2f}')

# ── 7. 표 8 참고문헌 ──
P('\n=== 표 8 참고문헌 (참고문헌 블록 보유 논문만) ===')
def intl(ref):
    s = ' '.join([ref.get('title') or '', ref.get('journal') or '', ref.get('author') or ''])
    return not re.search(r'[가-힣]', s)
rp, ip = [], []
for g in G:
    rows = [o for o in by[g] if o['r'].get('ref_available')]
    refs = [f for o in rows for f in o['r']['references']]
    rp.append(round(len(refs) / len(rows), 1) if rows else 0); ip.append(round(100 * sum(1 for f in refs if intl(f)) / len(refs), 1) if refs else 0)
    P(f'  {g}: 참고문헌 보유 {len(rows)}/{len(by[g])}편')
row3('편당 참고문헌', T['table8_refs']['refs_per_paper'], rp, '{:.1f}')
row3('국제문헌 %', T['table8_refs']['international_pct'], ip, '{:.1f}')

# ── 8. 표 9 기능비특정 초점 ──
P('\n=== 표 9 기능비특정 초점 (규칙 분류) ===')
FOCUS = [('교사·교육주체', re.compile(r'교사|교수자|교원|예비\s*교사|teacher|instructor|educator|양성|역할|professional', re.I)),
         ('학습자 인식·수용·정의적', re.compile(r'인식|태도|수용|만족|의도|불안|동기|perception|attitude|acceptance|intention|motivation|anxiety|TAM|UTAUT', re.I)),
         ('연구동향·메타분석', re.compile(r'동향|메타|체계적|문헌\s*고찰|review|trend|meta|bibliometric|scoping', re.I)),
         ('도구·자원 개발', re.compile(r'개발|설계|구축|플랫폼|시스템|모형|앱|develop|design|framework|system|platform', re.I))]
def focus(o):
    t = ' '.join([o['r']['title_ko'] or '', o['r']['title_en'] or '', o['r']['kw_ko'] or ''])
    for name, p in FOCUS:
        if p.search(t): return name
    return '일반 논의·활용 제언'
cfo = {g: Counter(o.get('focus') or focus(o) for o in by[g] if o['func'] == '기능비특정') for g in G}
for k, p in T['table9_nonspecific_focus'].items():
    if k == '합계': continue
    row3(k, p, [cfo[g][k] for g in G])

# ── 9. 4.3 키워드 공유·최초 출현 (근사) ──
P('\n=== 4.3 키워드 공유 (원시 키워드 소문자 정규화, 근사) ===')
def kws(o): return set(k.strip().lower() for k in re.split(r'[;,/]', (o['r']['kw_ko'] or '') + ';' + (o['r']['kw_en'] or '')) if k.strip())
KS = {g: set().union(*[kws(o) for o in by[g]]) for g in G}
P(f'세 군 공유 {len(KS["영어"] & KS["한국어"] & KS["중국어"])} (논문 16) | 영-한 {len(KS["영어"] & KS["한국어"])} (90) | 영-중 {len(KS["영어"] & KS["중국어"])} (20) | 한-중 {len(KS["한국어"] & KS["중국어"])} (16)  ※ 논문은 20개 개념으로 동의어 통합 후 산출')
TOPIC = {'AI 일반·챗봇·기계번역': r'챗봇|chatbot|기계\s*번역|machine translation|번역기|인공지능|\bAI\b',
         '생성형 AI·LLM': r'생성형|generative|\bLLM|chat\s*-?gpt|챗\s*gpt|언어\s*모델|language model',
         '음성·발음': r'음성\s*인식|speech recognition|\bTTS\b|음성\s*합성|발음|pronunciation|AI\s*스피커',
         '리터러시': r'리터러시|literacy|프롬프트\s*리터러시',
         '자동평가·피드백': r'자동\s*채점|자동\s*평가|automated (essay )?scoring|자동\s*피드백|automated feedback|\bAWE\b',
         '정책·에듀테크': r'에듀테크|edtech|디지털\s*교과서|digital textbook|AIDT|정책|policy'}
P('주제군 최초 출현 연도 (제목·주제어 기준 근사):')
for name, pat in TOPIC.items():
    p = re.compile(pat, re.I); fy = []
    for g in G:
        ys = [o['r']['year'] for o in by[g] if p.search(' '.join([o['r']['title_ko'] or '', o['r']['title_en'] or '', o['r']['kw_ko'] or '', o['r']['kw_en'] or '']))]
        fy.append(min(ys) if ys else None)
    tp = T['table3_first_year'][name]
    P(f'  {name:<16} 논문 {tp} | 재구성 {fy}')

# ── 10. 기타 본문 수치 ──
P('\n=== 본문 기타 ===')
P(f'쓰기 합계 {sum(cf[g]["쓰기"] for g in G)} (297) | 말하기 {sum(cf[g]["말하기"] for g in G)} (166) | 듣기 {sum(cf[g]["듣기"] for g in G)} (8) | 기능특정 합 {sum(npap)} (871)')
P(f'중국어 개발+성능 {cm["중국어"]["개발연구"]+cm["중국어"]["성능평가"]}편 = {100*(cm["중국어"]["개발연구"]+cm["중국어"]["성능평가"])/54:.1f}% (59.3%) | 중국어 실험 {cm["중국어"]["실험연구"]}편 (1) | 실험 178 중 영어 {cm["영어"]["실험연구"]}/{sum(cm[g]["실험연구"] for g in G)}')
open(f'{REPO}/analysis/check_paper_report' + ('_honest' if 'honest' in SRC else '') + '.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
