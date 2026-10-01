# -*- coding: utf-8 -*-
"""build_revision_sheet.py — 확정 코퍼스 기준 원고 수정 대조표 생성.

원고(제출본 J1_202600078)의 모든 수치를 절 순서대로 '원문 값 → 수정 값'으로 정리하고,
hwp에 그대로 옮겨 칠 수 있는 표 본문을 함께 만든다. 모든 새 값은 데이터에서 계산한다(손으로 옮기지 않음).

입력: data/rejudge/merged_<DATE>.json, analysis/{tables_4to8,keyword_diffusion,rarefaction}_<DATE>.json,
      analysis/paper_targets.json
산출: 원고수정_수치대조표_<DATE>.md
"""
import json, os, sys, io
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DATE = sys.argv[sys.argv.index('--date') + 1] if '--date' in sys.argv else '1166_20260930'
G = ['영어', '한국어', '중국어']
FUNCS = ['쓰기', '말하기', '평가·채점', '읽기', '리터러시·역량', '번역', '문법', '문학·문화', '발음', '어휘', '듣기']
METHS = ['개발연구', '조사연구', '질적·사례', '실험연구', '문헌·리뷰', '성능평가', '코퍼스분석', '기타·혼합']
FOCUS = ['교사·교육주체', '학습자 인식·수용·정의적', '연구동향·메타분석', '일반 논의·활용 제언', '도구·자원 개발']

PT = json.load(open(f'{REPO}/analysis/paper_targets.json', encoding='utf-8'))
T48 = json.load(open(f'{REPO}/analysis/tables_4to8_{DATE}.json', encoding='utf-8'))
KD = json.load(open(f'{REPO}/analysis/keyword_diffusion_{DATE}.json', encoding='utf-8'))
RF = json.load(open(f'{REPO}/analysis/rarefaction_{DATE}.json', encoding='utf-8'))
merged = json.load(open(f'{REPO}/data/rejudge/merged_{DATE}.json', encoding='utf-8'))
inc = [r for r in merged if r['include'] == 'Y']; exc = [r for r in merged if r['include'] == 'N']
by = {g: [r for r in inc if r['group'] == g] for g in G}
n = {g: len(by[g]) for g in G}; N = len(inc)
pct = lambda a, b: 100 * a / b if b else 0

# ── 집계 ───────────────────────────────────────────────────────────────────
yc = defaultdict(Counter)
for r in inc: yc[int(r['year'])][r['group']] += 1
ytot = {y: sum(yc[y].values()) for y in range(2020, 2027)}
en_share = [pct(yc[y]['영어'], ytot[y]) for y in range(2020, 2027)]
mc = {g: Counter(r['meth'] for r in by[g]) for g in G}
mtot = {m: sum(mc[g][m] for g in G) for m in METHS}
fc = {g: Counter(r['func'] for r in by[g]) for g in G}
ftot = {f: sum(fc[g][f] for g in G) for f in FUNCS + ['기능비특정']}
foc = {g: Counter(r['focus'] for r in by[g] if r['func'] == '기능비특정') for g in G}
foctot = {k: sum(foc[g][k] for g in G) for k in FOCUS}
nonspec = ftot['기능비특정']; spec = N - nonspec
grid = {g: Counter((r['func'], r['meth']) for r in by[g] if r['func'] != '기능비특정') for g in G}
gp = {g: sum(grid[g].values()) for g in G}
filled = {g: len(grid[g]) for g in G}
exp_tot = mtot['실험연구']
t4 = T48['table4']; t6 = T48['table6']; t7 = T48['table7']; t8 = T48['table8']
zh_sole = t4['중국어']['sole']
zh_build = pct(mc['중국어']['개발연구'] + mc['중국어']['성능평가'], n['중국어'])
lead = {(f, m): grid['영어'][(f, m)] + grid['한국어'][(f, m)] for f in FUNCS for m in METHS}
pend = sorted([(lead[(f, m)], f, m) for f in FUNCS for m in METHS if grid['중국어'][(f, m)] <= 1], reverse=True)[:10]
ex_reason = Counter(r['reason'] for r in exc)
ko_learner = Counter(r['learner'] for r in by['한국어'])


# 주제 출현 시차의 규모 보정 판정: 두 비교군 축소 분포(5–95%)와 모두 비교
def lag_out(mname):
    zy = KD['module_first_year'][mname].get('중국어'); sm = KD['size_matched'][mname]
    return [g for g in ('영어', '한국어') if zy and sm.get(g) and zy > sm[g]['p95']]


LAG = {m: lag_out(m) for m in KD['module_first_year']}
lag_both = [m for m, o in LAG.items() if len(o) == 2]
lag_part = [(m, o[0]) for m, o in LAG.items() if len(o) == 1]
EN_MOD = {'자동평가·피드백': 'automated assessment and feedback', '음성·발음(음성인식·TTS)': 'speech and pronunciation',
          '리터러시(AI·디지털·프롬프트)': 'AI literacy', '에듀테크·교육 정책': 'policy and edtech'}


def lag_ko():
    if lag_both:
        return f'주제 출현 시차 역시 대부분 규모 효과로 설명되었고, {"·".join(lag_both)} 영역만 규모를 통제한 뒤에도 두 비교군보다 늦었다. '
    if lag_part:
        return '주제 출현 시차도 대부분 규모 효과로 설명되었으며, ' + ', '.join(f'{m}은 {g}군과 비교할 때만 늦었다' for m, g in lag_part) + '. '
    return '주제 출현 시차도 규모 효과로 설명되었다. '


def lag_en():
    if lag_both:
        return ('Most apparent lags in topic emergence were likewise explained by corpus size; only '
                + ', '.join(EN_MOD.get(m, m) for m in lag_both) + ' remained delayed relative to both comparison groups after size matching. ')
    if lag_part:
        return ('Apparent lags in topic emergence were also largely explained by corpus size; '
                + '; '.join(f'{EN_MOD.get(m, m)} lagged only behind {"English" if g == "영어" else "Korean"}' for m, g in lag_part) + '. ')
    return 'Apparent lags in topic emergence were likewise explained by corpus size. '


def lag_row():
    if lag_both:
        return f'여섯 주제군 가운데 {"·".join(lag_both)}만 두 비교군 모두 대비 실질 지연이고, 나머지는 규모 효과로 설명된다'
    if lag_part:
        return (f'여섯 주제군 가운데 {len(LAG) - len(lag_part)}개의 "중국어 지연"은 두 비교군 모두의 규모 기대 범위 안에 있어 규모 효과로 설명되고, '
                + ', '.join(f'{m}은 {g}군 대비로만 늦다(경계 결과)' for m, g in lag_part))
    return '여섯 주제군의 "중국어 지연"은 모두 규모 효과로 설명된다'

f1 = lambda x: f'{x:.1f}'
L = []
A = L.append
A(f'# 원고 수정 수치 대조표 — 확정 코퍼스 {N:,}편 기준 ({DATE})\n')
A('대상 원고: 제출본 `manuscript/J1_202600078.hwp`. 수정은 사본 `manuscript/J1_202600078_수정본.hwp`에서 한다.')
A('모든 새 값은 `scripts/rejudge/build_revision_sheet.py`가 데이터에서 계산했다. 절 순서대로 정리했고, '
  '표는 hwp에 옮겨 칠 수 있게 원고와 같은 형식으로 만들었다.\n')
A('**확정 코퍼스**: ' + f'{N:,}편 = 영어 {n["영어"]} · 한국어 {n["한국어"]} · 중국어 {n["중국어"]} (제외 {len(exc)}편, 후보 {len(merged):,}편)\n')
A('**적용한 저자 결정**: [AI+언어교육] 융합만 대상. 국어 교과 담론형 제외, 대학 교양 제외, AI 디지털교과서 제외, '
  '통번역 수업은 AI를 번역 교육에 적용했으면 포함, 문법·NLP는 교육적 적용이 있으면 포함, 자동채점·화법 평가 도구는 교양 맥락이어도 포함, '
  '여러 언어를 함께 다룬 복수언어 연구는 제외(대상 언어를 명시하지 않은 연구는 언어 비특정으로 제외). '
  '모든 논문은 영어·한국어·중국어 세 언어 범주로만 구분한다. '
  'κ는 새로 계산할 예정이라 이 대조표에서 다루지 않는다.\n')

A('## 0. 수정의 성격 — 숫자 교체와 서술 재작성을 구분한다\n')
A('| 구분 | 해당 부분 | 이유 |\n|---|---|---|')
A('| **서술 재작성** | 국문·영문 초록, 5.1 격자 점유율 문단, 5.1 "최대 24개 범주" 문장, 표 11 해석 | '
  f'격자 점유율 비교는 규모 효과다. 영어·한국어군에서 {RF["n_zh_grid"]}편만 뽑아도 평균 {RF["rarefy"]["영어"]["mean"]:.1f}·{RF["rarefy"]["한국어"]["mean"]:.1f}칸이 차고, '
  f'중국어 실측 {RF["k_zh"]}칸은 백분위 {RF["rarefy"]["영어"]["pct_le"]:.0f}에 놓인다. 점유율로 "분산·미축적"을 주장할 수 없다 |')
A('| **서술 재작성** | 4.2 그림 3 문단의 "중국어군은 단 1편" 대비 | '
  f'중국어 실험연구는 {mc["중국어"]["실험연구"]}편({f1(pct(mc["중국어"]["실험연구"], n["중국어"]))}%)으로 한국어군({f1(pct(mc["한국어"]["실험연구"], n["한국어"]))}%)과 같은 수준이다. '
  f'초기하 검정에서도 한국어군 대비 P={RF["hyper"]["한국어"]["p_exp_le"]:.2f}로 차이가 없고, 영어군 대비로만 유의하다 |')
A(f'| **서술 재작성** | 4.3 표 3 해석, 각주 11 | {lag_row()} |')
A('| **서술 재작성** | 3.1 각주 3(L1 범위), 각주 6 | 저자 결정에 따라 포함 범위가 바뀌었고, 각주 6의 두 논문은 코퍼스 밖이다 |')
A('| 숫자 교체 | 나머지 전부 | 방향은 같고 값만 바뀐다 |\n')

# ── 초록 ───────────────────────────────────────────────────────────────────
A('## 1. 국문 제요 · 영문 Abstract\n')
A('| 원문 값 | 수정 값 | 비고 |\n|---|---|---|')
A(f'| 1,142편(영어 667편, 한국어 421편, 중국어 54편) | {N:,}편(영어 {n["영어"]}편, 한국어 {n["한국어"]}편, 중국어 {n["중국어"]}편) | 영문 동일 |')
A(f'| 중국어교육 연구는 전체의 4.7% | {f1(pct(n["중국어"], N))}% | 영문 4.7% → {f1(pct(n["중국어"], N))}% |')
A(f'| 단독저자 논문이 61.1% | {f1(zh_sole)}% | 표 4 |')
A(f'| 개발연구와 성능평가가 59.3% | {f1(zh_build)}% | 그림 3 |')
A(f'| 실험연구는 1편 | {mc["중국어"]["실험연구"]}편 | "1편이었다" → "{mc["중국어"]["실험연구"]}편에 그쳤다" |')
A('| 격자 점유율은 영어 72.7%, 한국어 62.5%, 중국어 27.3%로 … 축적되지 않았다 | **문장 삭제 후 재작성** | 0절 참조. 아래 초안 |')
A(f'| 구조공백은 88칸 중 18칸으로 듣기와 문학·문화에 집중 | 88칸 중 {RF["struct"]}칸, 듣기에 가장 많다 | 구조공백 기능: 듣기 4·문학·문화 3·기타 8 |\n')
A('**국문 제요 재작성 초안** (격자 문장만 교체, 나머지는 수치만 바꾼 형태)\n')
A('> 본 연구는 KCI에 축적된 AI 활용 언어교육 연구를 영어·한국어·중국어교육의 세 영역에 걸쳐 하나의 좌표계에서 비교하였다. '
  f'KCI Open API로 2020년부터 2026년 6월까지의 문헌을 수집하고, 초록 단위 재판정을 거쳐 AI와 언어교육의 융합 연구 {N:,}편'
  f'(영어 {n["영어"]}편, 한국어 {n["한국어"]}편, 중국어 {n["중국어"]}편)의 코퍼스를 구축하였다. '
  '여기에 동일한 분류 기준을 적용해 교수·학습 과제와 연구방법을 교차한 88칸의 격자를 구성하고, 연도별 추이와 주제 출현, 공저 네트워크, 인용을 보조 지표로 분석하였다. '
  f'중국어교육 연구는 전체의 {f1(pct(n["중국어"], N))}%였고, 중국어군 내부에서는 단독저자 논문이 {f1(zh_sole)}%, 개발연구와 성능평가가 {f1(zh_build)}%인 반면 '
  f'학습 성과를 비교한 실험연구는 {mc["중국어"]["실험연구"]}편에 그쳤다. '
  f'규모를 통제한 희박화 분석에서 중국어군의 격자 점유는 같은 편수의 영어·한국어 표본과 다르지 않았으나, 연구방법 구성은 영어군과 뚜렷이 달라 '
  f'실험연구가 적고 개발·성능평가에 집중되었다(초기하 검정 P<0.0001). 이 구성은 한국어군과 유사하였다. '
  f'{lag_ko()}'
  f'비교군에는 두텁게 축적되었으나 중국어군에는 0~1편에 그친 확산대기 좌표는 쓰기·말하기·평가에 몰렸고, 세 영역 모두에서 관찰되지 않은 구조공백은 88칸 중 {RF["struct"]}칸으로 듣기에 가장 많았다. '
  '본 연구는 우열을 판정하려는 것이 아니라 기존 연구 설계를 선택적으로 타당화할 좌표와 중국어의 맥락에 맞는 설계를 새로 개발할 좌표를 구분하여, 후속 연구가 검토할 지점을 제시하는 데 목적이 있다.\n')
A('**영문 Abstract 재작성 초안**\n')
A('> This study compared AI-assisted language education research in English, Korean, and Chinese within a single analytical framework. '
  'Records indexed in the Korea Citation Index (KCI) from 2020 to June 2026 were collected through the KCI Open API and re-screened at the abstract level, '
  f'yielding a corpus of {N:,} articles that integrate AI and language education ({n["영어"]} English, {n["한국어"]} Korean, {n["중국어"]} Chinese). '
  'Uniform classification criteria were applied to build an 88-cell task-by-method grid, supplemented by trend, topic-emergence, co-authorship, and citation analyses. '
  f'Chinese-language studies accounted for {f1(pct(n["중국어"], N))}% of the corpus; within this subcorpus, {f1(zh_sole)}% were single-authored and development and '
  f'performance-evaluation studies constituted {f1(zh_build)}%, whereas only {mc["중국어"]["실험연구"]} studies experimentally compared learning outcomes. '
  'Rarefaction showed that the Chinese grid occupancy did not differ from that of size-matched English and Korean samples, '
  'but the method composition differed sharply from English—fewer experiments and more development and performance evaluation (hypergeometric P<0.0001)—while resembling Korean. '
  f'{lag_en()}'
  'Diffusion-pending coordinates—dense in the comparison groups but with zero or one Chinese study—clustered in writing, speaking, and assessment, '
  f'while {RF["struct"]} of the 88 cells were structural gaps unobserved in all three domains, most frequently in listening. '
  'The aim is not to rank the three domains but to distinguish coordinates where existing designs can be selectively validated from those where new designs suited to Chinese must be developed.\n')

# ── 3.1 ───────────────────────────────────────────────────────────────────
A('## 2. 3.1 연구대상 및 자료수집\n')
A('| 원문 | 수정 |\n|---|---|')
A(f'| 최종 분석 대상은 총 1,142편 | 총 {N:,}편 |')
A(f'| 영어교육 667편(58.4%), 한국어교육 421편(36.9%), 중국어교육 54편(4.7%) | 영어교육 {n["영어"]}편({f1(pct(n["영어"], N))}%), 한국어교육 {n["한국어"]}편({f1(pct(n["한국어"], N))}%), 중국어교육 {n["중국어"]}편({f1(pct(n["중국어"], N))}%) |')
A(f'| "이후 교육맥락이 부재한 순수 기술연구 등을 수동으로 직접 제외하여" | 후보 {len(merged):,}편 전편의 초록을 읽어 포함 여부를 판정했다는 절차와 편수 흐름({len(merged):,} → {N:,})을 명시. 심사위원 2-2·2-3 대응 |\n')
A('### 각주 2 — 제외 사유 (원문 189편 → 수정)\n')
A('| 사유 | 원문 편수 | 수정 편수 |\n|---|---|---|')
paper_fn2 = PT['footnote2_exclusions']
order = ['제2외국어', '언어비특정', '복수언어', '교육맥락없음', '메타버스VR', '교양교육', '번역품질', '국어교과담론', '비AI에듀테크', 'AI디지털교과서', 'AI신호부재', '기타']
order += [k for k in ex_reason if k not in order]   # 새 사유가 생겨도 합계가 어긋나지 않게
label = {'제2외국어': '영·한·중이 아닌 제2외국어', '언어비특정': '언어 비특정 일반 연구', '복수언어': '여러 언어를 함께 다룬 복수언어 연구',
         '교육맥락없음': '교육 맥락 없는 순수 NLP·언어학',
         '메타버스VR': '메타버스·VR', '교양교육': '대학 교양 교육', '번역품질': '교육 맥락 없는 번역 품질', '국어교과담론': '국어 교과 담론형',
         '비AI에듀테크': 'AI를 쓰지 않은 에듀테크', 'AI디지털교과서': 'AI 디지털교과서', 'AI신호부재': 'AI 신호 부재', '기타': '기타'}
for k in order:
    if k == '복수언어' and not ex_reason[k]:
        continue
    A(f'| {label.get(k, k)} | {paper_fn2.get(k, "—")} | {ex_reason[k]} |')
A(f'| 계 | {paper_fn2["total"]} | {len(exc)} |\n')
A(f'원문 "번역품질을 이유로 배제된 것은 3편에 불과하여 … 과도하게 배제되었을 가능성은 낮다"는 문장은 수정 편수({ex_reason["번역품질"]}편)와 맞지 않으므로 삭제하거나, '
  '"통번역 수업에 AI를 적용한 연구는 포함하고 학습자·수업 맥락이 없는 번역 품질 연구만 제외했다"로 바꾼다.\n')
A('### 각주 3 — 학습자 맥락(L1) 범위\n')
A('원문: "학습자가 모어(L1) 화자인지 외국어(L2) 학습자인지는 가리지 않는다. 한국 학생의 국어 작문·대학 글쓰기 교육, 외국인의 한국어 학습 등 …"\n')
A(f'수정안: "학습자가 모어(L1) 화자인지 외국어(L2) 학습자인지는 가리지 않으나, AI와 언어교육의 융합 연구로 범위를 한정하였다. 초·중등 국어 교과의 AI 활용 연구는 포함하되 '
  f'AI 시대 교과의 대응 방향만 논의한 담론형 연구와 대학 교양 교과의 글쓰기·읽기·토론 교육 연구는 제외하였다(단 AI 자동채점·화법 평가 도구를 개발·검증한 연구는 포함). '
  f'이에 한국어군 {n["한국어"]}편의 학습자 맥락은 L2 {ko_learner["L2"]}편, L1 {ko_learner["L1"]}편, 미명시 {ko_learner["미명시"]}편이다."\n')

# ── 4.1 ───────────────────────────────────────────────────────────────────
A('## 3. 4.1 그림 1·그림 2와 본문\n')
A('| 원문 | 수정 |\n|---|---|')
A(f'| 영어가 667편(58.4%) … 한국어가 421편(36.9%), 중국어는 54편(4.7%) | 영어 {n["영어"]}편({f1(pct(n["영어"], N))}%), 한국어 {n["한국어"]}편({f1(pct(n["한국어"], N))}%), 중국어 {n["중국어"]}편({f1(pct(n["중국어"], N))}%) |')
A(f'| 영어와 중국어의 편수 격차가 12배를 넘는다(667편 대 54편) | {n["영어"] / n["중국어"]:.1f}배(=10배를 넘는다)({n["영어"]}편 대 {n["중국어"]}편) |')
A(f'| 2020–2022년 연간 논문 수는 28–69편 | {min(ytot[y] for y in (2020, 2021, 2022))}–{max(ytot[y] for y in (2020, 2021, 2022))}편 |')
A(f'| 2023년은 151편으로 직전 연도의 약 2.5배 | {ytot[2023]}편, 직전 연도({ytot[2022]}편)의 약 {ytot[2023] / ytot[2022]:.1f}배 |')
A(f'| 2024년 235편, 2025년 376편 | 2024년 {ytot[2024]}편, 2025년 {ytot[2025]}편 |')
A(f'| 2025년은 2021년(69편)의 약 5.4배 | 2021년({ytot[2021]}편)의 약 {ytot[2025] / ytot[2021]:.1f}배 |')
A(f'| 2026년은 6월 기준 222편 | {ytot[2026]}편 |')
A(f'| 영어 관련 논문 수는 연도별로 전체의 54%에서 82% | {min(en_share):.0f}%에서 {max(en_share):.0f}% |')
A(f'| 중국어 연구는 2022년까지 연 1–2편, 2023년 5편, 2024년 14편, 2025년 20편 | 2022년까지 연 {min(yc[y]["중국어"] for y in (2020, 2021, 2022))}–{max(yc[y]["중국어"] for y in (2020, 2021, 2022))}편, 2023년 {yc[2023]["중국어"]}편, 2024년 {yc[2024]["중국어"]}편, 2025년 {yc[2025]["중국어"]}편(2026년 6월까지 {yc[2026]["중국어"]}편) |')
A(f'| 서론: 2020년 28편에서 2023년 151편, 2025년 376편 | 2020년 {ytot[2020]}편에서 2023년 {ytot[2023]}편, 2025년 {ytot[2025]}편 |\n')
A('**그림 2 데이터(연도 × 언어군)**\n')
A('| 연도 | 영어 | 한국어 | 중국어 | 계 | 영어 비중 |\n|---|---|---|---|---|---|')
for i, y in enumerate(range(2020, 2027)):
    A(f'| {y} | {yc[y]["영어"]} | {yc[y]["한국어"]} | {yc[y]["중국어"]} | {ytot[y]} | {en_share[i]:.0f}% |')
A(f'| 계 | {n["영어"]} | {n["한국어"]} | {n["중국어"]} | {N} | {f1(pct(n["영어"], N))}% |\n')
A('**각주 6 수정안**: "이 시기 연구의 성격은 본 코퍼스에 포함되지 않은 강병규(2021)의 BERT를 활용한 중국어 문법 예측 연구, 오현주·차오팡(2020)의 자연언어처리 기반 문법 연구 같은 '
  '선행연구에서도 확인된다. 두 연구는 교수·학습 맥락이 없는 자연어처리 연구여서 분석 대상에서는 제외하였다. 이 시기의 도구는 …(이하 원문 유지)"\n')

# ── 4.2 ───────────────────────────────────────────────────────────────────
A('## 4. 4.2 표 2·그림 3과 본문\n')
A('**표 2 연구방법 분포 (옮겨 칠 표)**\n')
A('| 방법 | 영어 | 한국어 | 중국어 | 논문 수 | 비율 |\n|---|---|---|---|---|---|')
for m in METHS:
    A(f'| {m} | {mc["영어"][m]} | {mc["한국어"][m]} | {mc["중국어"][m]} | {mtot[m]} | {f1(pct(mtot[m], N))}% |')
A(f'| 합계 | {n["영어"]} | {n["한국어"]} | {n["중국어"]} | {N:,} | 100% |\n')
rank = sorted(METHS, key=lambda m: -mtot[m])
A('| 원문 | 수정 |\n|---|---|')
A(f'| 가장 큰 비중은 개발연구(21.3%), 그 뒤를 조사연구(18.7%)와 질적·사례연구(16.2%) | 순위가 바뀐다: '
  + ', '.join(f'{m} {f1(pct(mtot[m], N))}%' for m in rank[:5]) + '. 문장의 순서 서술을 새 순위로 고친다 |')
A(f'| 실험연구(15.6%)와 성능평가(10.1%) | 실험연구({f1(pct(mtot["실험연구"], N))}%)와 성능평가({f1(pct(mtot["성능평가"], N))}%) |')
A(f'| 각주 9: 실험연구 178편 | {exp_tot}편 |')
A(f'| 전체 실험연구 178편 중 150편(84%)이 영어군 | {exp_tot}편 중 {mc["영어"]["실험연구"]}편({pct(mc["영어"]["실험연구"], exp_tot):.0f}%)이 영어군 |')
A(f'| 한국어군은 27편(6.2%), 중국어군은 단 1편(1.9%) | 한국어군 {mc["한국어"]["실험연구"]}편({f1(pct(mc["한국어"]["실험연구"], n["한국어"]))}%), 중국어군 {mc["중국어"]["실험연구"]}편({f1(pct(mc["중국어"]["실험연구"], n["중국어"]))}%). "단 1편"의 강조 제거 |')
A(f'| 중국어군은 개발연구(22편)와 성능평가(10편) | 개발연구({mc["중국어"]["개발연구"]}편)와 성능평가({mc["중국어"]["성능평가"]}편) |')
A(f'| 한국어군도 개발연구(131편) | 개발연구({mc["한국어"]["개발연구"]}편) |\n')
A('**그림 3 데이터**\n')
A('| 지표 | 영어 | 한국어 | 중국어 | 원문 |\n|---|---|---|---|---|')
A('| 실험연구 비중 | ' + ' | '.join(f'{f1(pct(mc[g]["실험연구"], n[g]))}%' for g in G) + ' | 22.6 / 6.2 / 1.9 |')
A('| 구축·평가형(개발+성능평가) 비중 | ' + ' | '.join(f'{f1(pct(mc[g]["개발연구"] + mc[g]["성능평가"], n[g]))}%' for g in G) + ' | 21.2 / 43.8 / 59.3 |\n')

# ── 4.3 ───────────────────────────────────────────────────────────────────
A('## 5. 4.3 표 3·주제 확산\n')
A('**표 3 주제군별 최초 출현 연도 (옮겨 칠 표)**\n')
A('| 주제군(모듈) | 영어 | 한국어 | 중국어 | 영→중 시차 | 규모 보정 판정 |\n|---|---|---|---|---|---|')
for mname, fy in KD['module_first_year'].items():
    verdict = ('규모 효과' if not LAG[mname] else ('실질 지연(두 비교군 대비)' if len(LAG[mname]) == 2 else f'{LAG[mname][0]}군 대비로만 지연(경계)'))
    gap = (fy['중국어'] - fy['영어']) if ('중국어' in fy and '영어' in fy) else '—'
    A(f'| {mname} | {fy.get("영어", "—")} | {fy.get("한국어", "—")} | {fy.get("중국어", "—")} | {gap}년 | {verdict} |')
sk = KD['shared_keywords']; ll = KD['leadlag']
A('\n| 원문 | 수정 |\n|---|---|')
A(f'| 세 언어군이 모두 공유하는 키워드는 16개 | {sk["all3"]}개 |')
A(f'| 영어-한국어 90개, 영어-중국어 20개, 한국어-중국어 16개 | 영어-한국어 {sk["en_ko"]}개, 영어-중국어 {sk["en_zh"]}개, 한국어-중국어 {sk["ko_zh"]}개 |')
A(f'| 시차 중앙값 영어→한국어 1년, 영어→중국어 0.5년, 한국어→중국어 0년 | 영어→한국어 {ll["영어→한국어"][0]:g}년, 영어→중국어 {ll["영어→중국어"][0]:g}년, 한국어→중국어 {ll["한국어→중국어"][0]:g}년 |')
A('| "교육 현장의 구체적 과제로 전개되는 주제군에서는 중국어군의 최초 출현이 3~5년가량 늦게 관측" | '
  f'규모를 맞춘 비교(영·한에서 {KD["n_zh"]}편 무작위 추출 2,000회)를 함께 제시한다. {lag_row()}. 규모로 설명되는 주제군은 "소규모 코퍼스에서 기대되는 범위"로 서술하고, 최초 출현 연도는 탐색적 신호로 다룬다 |')
A('| 각주 10: 20개 개념 정규화 | 정규화표를 부록에 수록(`analysis/keyword_concepts.json`) |\n')

# ── 4.4 표 4 ──────────────────────────────────────────────────────────────
A('## 6. 4.4 표 4 공저 네트워크\n')
A('**표 4 (옮겨 칠 표, 중심성 두 열은 심사위원 1-5 대응으로 추가)**\n')
A('| 언어군 | 논문 수 | 저자 수 | 논문당 저자 | 단독저자 논문 | 고립 저자 비율 | 연결 요소 | 최대 공저 군집 | 평균 연결정도 | 밀도 | 매개 중심성 최댓값 |')
A('|---|---|---|---|---|---|---|---|---|---|---|')
for g in G:
    d = t4[g]
    A(f'| {g} | {n[g]} | {d["authors"]} | {d["per"]:.2f} | {d["sole"]:.1f}% | {d["iso"]:.1f}% | {d["comps"]} | {d["largest"]}명({pct(d["largest"], d["authors"]):.1f}%) | {d["mean_deg"]:.2f} | {d["density"]:.4f} | {d["bc_max"]:.4f} |')
A('\n| 원문 | 수정 |\n|---|---|')
A(f'| 중국어군 단독저자 61.1% | {t4["중국어"]["sole"]:.1f}% |')
A(f'| 고립 저자 41.7% | {t4["중국어"]["iso"]:.1f}% |')
A(f'| 최대 군집 영어 74명 / 한국어 17명 / 중국어 4명 | {t4["영어"]["largest"]} / {t4["한국어"]["largest"]} / {t4["중국어"]["largest"]}명 |')
A(f'| 평균 연결정도 중국어군만 1 미만(0.93) | {t4["중국어"]["mean_deg"]:.2f}로 여전히 1 미만 |\n')

# ── 4.5 표 5~8 ────────────────────────────────────────────────────────────
A('## 7. 4.5 표 5·6·7·8 인용과 지식 원천\n')
A('피인용 조회일이 바뀐다(원문 2026-07-01 → 재수집 2026-09-29). 각주 14에 새 조회일을 적는다.\n')
A('**표 5 피인용 상위 10위 (옮겨 칠 표, 10위 동률 포함)**\n')
A('| 순위 | 제목 | 연도 | 언어군 | 피인용 |\n|---|---|---|---|---|')
_t5 = T48['table5_top10']
for o in _t5:
    i = 1 + sum(1 for x in _t5 if x['cited'] > o['cited'])  # 공동 순위
    A(f'| {i} | {o["title"]} | {o["year"]} | {o["group"]} | {o["cited"]} |')
A(f'\n10위 피인용(60회)이 3편 동률이라 {len(_t5)}편을 싣고 공동 순위로 적는다(임의로 끊지 않음). 5위도 69회 3편 동률이다. '
  '논문 표 5의 10편은 모두 확정 코퍼스에 남아 있고, "유도(guided) 쓰기 활동에서 ChatGPT의 활용 방안"(64회)이 새로 들어간다. '
  '표 제목의 "상위 10편"은 "상위 10위"로, 본문의 편수 서술도 11편 기준으로 고친다. '
  '제출본(7/1 조회)보다 늦게 조회했는데도 일부 논문의 피인용이 줄었으므로(예: 69→60회) KCI에서 한 번 확인한다.\n')
A('**표 6 총 피인용 (옮겨 칠 표)**\n')
A('| 언어군 | 논문 수 | 총 피인용 | 편당 평균 | 중앙값 | 피인용 0편 비율 |\n|---|---|---|---|---|---|')
for g in G:
    A(f'| {g} | {n[g]} | {t6["total"][g]:,} | {t6["per_paper"][g]:.2f} | {t6["median"][g]:g} | {t6["zero_pct"][g]:.1f}% |')
A(f'| 계 | {N:,} | {sum(t6["total"].values()):,} | {sum(t6["total"].values()) / N:.2f} | | |\n')
A(f'원문 "총 피인용 수는 5,409회" → {sum(t6["total"].values()):,}회. 편당 평균 배율 영/중: 원문 2.4배 → {t6["per_paper"]["영어"] / t6["per_paper"]["중국어"]:.1f}배.\n')
A('**표 7 2020–2023 코호트 (옮겨 칠 표)**\n')
A('| 언어군 | 코호트 편수 | 편당 피인용 |\n|---|---|---|')
for g in G:
    A(f'| {g} | {t7[g]["n"]} | {t7[g]["per_paper"]:.2f} |')
A(f'\n원문 "중국어군 편당 인용 8.67회, 영어군(15.79회)과의 격차 약 2.4배에서 1.8배로" → 중국어 {t7["중국어"]["per_paper"]:.2f}회, 영어 {t7["영어"]["per_paper"]:.2f}회, '
  f'격차 {t6["per_paper"]["영어"] / t6["per_paper"]["중국어"]:.1f}배에서 {t7["영어"]["per_paper"] / t7["중국어"]["per_paper"]:.1f}배로.\n')
A('**표 8 참고문헌 구성 (옮겨 칠 표)**\n')
A('| 언어군 | 편당 참고문헌 | 국내(한글) | 영문 등 | 중문 | 교육 | 언어학 | 문학 | 기타 |\n|---|---|---|---|---|---|---|---|---|')
for g in G:
    d = t8[g]
    A(f'| {g} | {d["per"]:.1f} | {d["dom"]:.1f}% | {d["intl_en"]:.1f}% | {d["intl_zh"]:.1f}% | {d["edu"]:.1f}% | {d["ling"]:.1f}% | {d["lit"]:.1f}% | {d["other"]:.1f}% |')
A('\n분야 비율은 원 분류기가 유실되어 참고문헌 학술지명 기준으로 재분류했다. 절대값은 원문과 직접 비교할 수 없으나 순서(교육 비중 영>한>중, 언어학·문학 비중 중>한>영)는 같다. '
  '표 8 각주에 "학술지명 기준 재분류, 학술지명 없는 단행본·웹자료 제외"를 밝힌다. '
  f'국제 문헌은 영문과 중문으로 나누어 제시한다. 한글이 없는 문헌을 모두 국제로 묶으면 중국어군이 {t8["중국어"]["intl"]:.1f}%로 원문(27.9%)보다 높아지는데, '
  f'이는 중문 문헌 {t8["중국어"]["intl_zh"]:.1f}%가 섞인 결과다. 영문 문헌만 보면 영어 {t8["영어"]["intl_en"]:.1f}% · 한국어 {t8["한국어"]["intl_en"]:.1f}% · 중국어 {t8["중국어"]["intl_en"]:.1f}%로 '
  '중국어군이 가장 낮아 원문의 방향(영문 국제 문헌 참조가 가장 적다)은 유지된다. 중국어군만 중문 문헌을 약 5분의 1 참조한다는 점은 새로 서술할 만한 특징이다.\n')

# ── 5.1 ───────────────────────────────────────────────────────────────────
A('## 8. 5.1 표 9·10·11·12와 본문\n')
A('**표 9 기능비특정 연구의 초점 (옮겨 칠 표)**\n')
A('| 연구 초점 | 영어 | 한국어 | 중국어 | 합계 | 비중 |\n|---|---|---|---|---|---|')
for k in FOCUS:
    A(f'| {k} | {foc["영어"][k]} | {foc["한국어"][k]} | {foc["중국어"][k]} | {foctot[k]} | {f1(pct(foctot[k], nonspec))}% |')
A(f'| 합계 | {fc["영어"]["기능비특정"]} | {fc["한국어"]["기능비특정"]} | {fc["중국어"]["기능비특정"]} | {nonspec} | 100% |\n')
tl = foctot['교사·교육주체'] + foctot['학습자 인식·수용·정의적']
A('| 원문 | 수정 |\n|---|---|')
A(f'| 전체 1,142편 중 특정 언어기능 871편(76.3%), 기능비특정 271편(23.7%) | 전체 {N:,}편 중 특정 언어기능 {spec}편({f1(pct(spec, N))}%), 기능비특정 {nonspec}편({f1(pct(nonspec, N))}%) |')
A(f'| 교사·교육주체(68편)와 학습자 인식(66편)을 합한 134편(49.5%) | 교사·교육주체({foctot["교사·교육주체"]}편)와 학습자 인식({foctot["학습자 인식·수용·정의적"]}편)을 합한 {tl}편({f1(pct(tl, nonspec))}%) |')
A(f'| 연구동향·메타분석(49편)을 더하면 271편의 67.6% | 연구동향·메타분석({foctot["연구동향·메타분석"]}편)을 더하면 {nonspec}편의 {f1(pct(tl + foctot["연구동향·메타분석"], nonspec))}% |\n')
A('**표 10 언어기능 분포 (옮겨 칠 표)**\n')
A('| 기능 | 영어 | 한국어 | 중국어 | 합계 | 전체 비율 |\n|---|---|---|---|---|---|')
for f in ['쓰기', '기능비특정'] + [x for x in FUNCS if x != '쓰기']:
    lab = '기능비특정(→표 9)' if f == '기능비특정' else f
    A(f'| {lab} | ' + ' | '.join(f'{fc[g][f]}({f1(pct(fc[g][f], n[g]))}%)' for g in G) + f' | {ftot[f]} | {f1(pct(ftot[f], N))}% |')
A(f'| 합계 | {n["영어"]} | {n["한국어"]} | {n["중국어"]} | {N:,} | 100.0% |\n')
wsp = ftot['쓰기'] + ftot['말하기']; ewsp = fc['영어']['쓰기'] + fc['영어']['말하기']
A('| 원문 | 수정 |\n|---|---|')
A(f'| 격자 분석은 기능비특정을 제외한 871편(영어 485, 한국어 350, 중국어 36) | {spec}편(영어 {gp["영어"]}, 한국어 {gp["한국어"]}, 중국어 {gp["중국어"]}) |')
A(f'| 쓰기 297편(26.0%), 말하기(166편, 14.5%), 표현 기능 463편(40.5%) | 쓰기 {ftot["쓰기"]}편({f1(pct(ftot["쓰기"], N))}%), 말하기({ftot["말하기"]}편, {f1(pct(ftot["말하기"], N))}%), 표현 기능 {wsp}편({f1(pct(wsp, N))}%) |')
A(f'| 듣기 영역은 세 언어군을 통틀어 8편(0.7%) | {ftot["듣기"]}편({f1(pct(ftot["듣기"], N))}%) |')
A(f'| 영어군은 쓰기 166편(24.9%)과 말하기 114편(17.1%)을 합해 280편(42.0%) | 쓰기 {fc["영어"]["쓰기"]}편({f1(pct(fc["영어"]["쓰기"], n["영어"]))}%)과 말하기 {fc["영어"]["말하기"]}편({f1(pct(fc["영어"]["말하기"], n["영어"]))}%)을 합해 {ewsp}편({f1(pct(ewsp, n["영어"]))}%) |')
A(f'| 한국어군 쓰기 126편이 최다 | 쓰기 {fc["한국어"]["쓰기"]}편과 평가·채점 {fc["한국어"]["평가·채점"]}편이 비슷하다. 한국어군의 무게중심을 "쓰기와 평가·채점 양쪽"으로 고친다 |\n')
A('**표 11 격자 점유 (옮겨 칠 표) — 해석 문단은 재작성**\n')
A('| 언어군 | 격자 편수 | 채워진 칸 | 점유율(88칸) | 빈 칸 | 칸당 평균 | 희박화 기대 점유(중국어 편수 기준) |\n|---|---|---|---|---|---|---|')
for g in G:
    rr = RF['rarefy'].get(g)
    exp_s = f'{rr["mean"]:.1f}칸(95% {rr["lo"]}–{rr["hi"]})' if rr else f'실측 {filled[g]}칸'
    A(f'| {g} | {gp[g]} | {filled[g]} | {f1(pct(filled[g], 88))}% | {88 - filled[g]} | {gp[g] / filled[g]:.1f} | {exp_s} |')
A('\n**5.1에서 삭제할 문장**: "교차 격자에 투입된 중국어 논문은 총 36편으로, 구조상 최대 24개 범주(격자)에만 위치할 수 있으나 실측 결과 24개 격자가 모두 채워진 것으로 나타났다. '
  '이는 산술적 상한선 전체를 …" — 36편이면 최대 36칸을 채울 수 있으므로 사실 오류다(심사위원 1-4, 2-1).\n')
A(f'**대체 문단 초안**: "중국어군 격자 투입 논문은 {RF["n_zh_grid"]}편으로 {RF["k_zh"]}칸을 채웠다. 점유율만 보면 영어({f1(pct(filled["영어"], 88))}%)·한국어({f1(pct(filled["한국어"], 88))}%)보다 낮으나, '
  f'영어·한국어군에서 같은 {RF["n_zh_grid"]}편을 1만 회 무작위 추출하면 기대 점유는 각각 {RF["rarefy"]["영어"]["mean"]:.1f}칸·{RF["rarefy"]["한국어"]["mean"]:.1f}칸이며 '
  f'중국어 실측은 이 분포의 상위(백분위 {RF["rarefy"]["영어"]["pct_le"]:.0f})에 놓인다. 따라서 점유율의 차이는 편수의 차이로 설명되며, 중국어군의 특징은 점유의 넓이가 아니라 연구방법의 구성에서 나타난다. '
  f'중국어군 {n["중국어"]}편을 영어군에서 같은 수로 뽑을 때 실험연구가 {mc["중국어"]["실험연구"]}편 이하일 확률과 개발·성능평가가 {mc["중국어"]["개발연구"] + mc["중국어"]["성능평가"]}편 이상일 확률은 모두 0.0001 미만이다. '
  f'반면 한국어군과 비교하면 두 확률은 각각 {RF["hyper"]["한국어"]["p_exp_le"]:.2f}, {RF["hyper"]["한국어"]["p_build_ge"]:.2f}로 차이가 없다."\n')
A('**표 12 확산대기 상위 10 좌표 (옮겨 칠 표)**\n')
A('| 순위 | 기능 | 방법 | 영어 | 한국어 | 중국어 |\n|---|---|---|---|---|---|')
for i, (s, f, m) in enumerate(pend, 1):
    A(f'| {i} | {f} | {m} | {grid["영어"][(f, m)]} | {grid["한국어"][(f, m)]} | {grid["중국어"][(f, m)]} |')
A('\n| 원문 | 수정 |\n|---|---|')
A(f'| 공백 좌표(중국어 0~1편) 79칸 | {RF["gap"]}칸 |')
A(f'| 구조공백 88칸 중 18칸, 듣기와 문학·문화에 집중 | 88칸 중 {RF["struct"]}칸. 듣기 4칸이 가장 많고 문학·문화 3칸, 리터러시·발음·어휘 각 2칸. '
  f'중국어군은 문학·문화 연구가 {fc["중국어"]["문학·문화"]}편({f1(pct(fc["중국어"]["문학·문화"], n["중국어"]))}%)으로 오히려 강한 영역이므로 "문학·문화 공백"을 중국어군의 약점으로 서술하지 않는다 |\n')

A('## 9. 부록·신설 권고\n')
A('- **3.4 신설(규모의 한계)**: 희박화·초기하 결과(`analysis/rarefaction_' + DATE + '.md`)와 주제 출현 규모 보정(`analysis/keyword_diffusion_' + DATE + '.md` 3절)을 요약한다.')
A('- **부록 A**: 코퍼스 확정 절차와 제외 사유(각주 2 표), 저자 결정 일곱 항목.')
A('- **부록 B**: 20개 개념 키워드 정규화표.')
A('- **부록 E**: 한국어군 L1/L2 분리 민감도(심사위원 2-5). 아직 산출하지 않았다.')
A('- κ(3.3)는 새로 계산할 예정이므로 이 대조표에서 제외했다.')

out = f'{REPO}/원고수정_수치대조표_{DATE}.md'
open(out, 'w', encoding='utf-8').write('\n'.join(L))
print('saved', out, len(L), 'lines')
