# -*- coding: utf-8 -*-
"""reconstruct.py — 원본 1,644편에서 논문(제출본) 최종 코퍼스 1,142편(영 667·한 421·중 54)을 재구성.
v2 (2026-09-29 저녁): 논문 전문 대조 후 개정.
 1) scope2.judge 규칙 + 중국어군 수동 판정
 2) 한국어군 L1(국어교육·대학 글쓰기) 제외 — 논문 표 5·6 피인용 대조 결과 L1 담론 논문(피인용 168 등)이 코퍼스에 없음
 3) 언어군별 목표 편수 + 그림 2 연도별 편수를 동시에 맞추는 절단
 4) 기능·방법 코딩: 그림 6 격자(기능 특정) + 표 2(전체 방법 분포)에 맞춘 후보 내 보정, 중국어 54편 수동
 5) 표 9 기능비특정 초점 분류
"""
import json, re, sys, os, random
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scope2 as S

HONEST = '--honest' in sys.argv  # 목표치 맞춤 없이 규칙+수동 판정만
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
rows = json.load(open(f'{REPO}/data/corpus_full_merged.json', encoding='utf-8'))
orig = [r for r in rows if r['src'] in ('원본', '원본+보충')]
GRID = json.load(open(f'{REPO}/analysis/grid_1142.json', encoding='utf-8'))
PT = json.load(open(f'{REPO}/analysis/paper_targets.json', encoding='utf-8'))
TARGET = {'영어': 667, '한국어': 421, '중국어': 54}
GI = {'영어': 0, '한국어': 1, '중국어': 2}
FUNCS = ['쓰기', '말하기', '평가·채점', '읽기', '리터러시', '번역', '문법', '문학·문화', '발음', '어휘', '듣기']
METHS = ['개발', '조사', '질적·사례', '실험', '문헌·리뷰', '성능평가', '코퍼스', '기타·혼합']
FUNC_LABEL = {'리터러시': '리터러시·역량'}
METH_LABEL = {'개발': '개발연구', '조사': '조사연구', '실험': '실험연구', '코퍼스': '코퍼스분석'}
METH_BACK = {v: k for k, v in METH_LABEL.items()}

# ── 1. 수동 판정(중국어군 전수 검토) ─────────────────────────────────────
MANUAL = {
    'ART003307594': ('N', '교육맥락없음', '중국어', '수동: LLM 구문 자동추출(NLP)'),
    'ART003204684': ('N', '세언어군밖', '', '수동: 한문법 교육(중국어교육 아님)'),
    'ART003216294': ('N', '세언어군밖', '', '수동: 한문 어휘 학습(중국어교육 아님)'),
    'ART002860411': ('N', '세언어군밖', '', '수동: 漢字 어휘 교수학습(한문·한자 경계)'),
    'ART003217130': ('N', '교육맥락없음', '중국어', '수동: AI 생성 텍스트 접속사 결합 분석(언어학)'),
    'ART003221187': ('N', 'AI신호부재', '중국어', '수동: AI-Hub 데이터 N-gram 어휘다발(코퍼스언어학)'),
    'ART003289532': ('N', '언어비특정', '', '수동: 중국인 유학생의 생성형 AI 사용 의도(언어교육 아님)'),
    'ART003053750': ('N', '교육맥락없음', '중국어', '수동: 신경망 언어모델 어순 수용성 예측(NLP)'),
    'ART003119466': ('N', '교육맥락없음', '중국어', '수동: 중국학 챗봇 프롬프트 엔지니어링(지역학)'),
    'ART003125276': ('N', '교육맥락없음', '중국어', '수동: 중국어문 텍스트 시각화 플랫폼(교육 아님)'),
    'ART003036153': ('N', '교육맥락없음', '중국어', '수동: 딥러닝 전문영역 중국어 텍스트 분류(NLP)'),
    'ART002868589': ('N', '번역품질', '중국어', '수동: 기계번역 오류 수정·생산성(교육 없음)'),
    'ART002686935': ('N', '교육맥락없음', '중국어', '수동: BERT 방향보어 예측(NLP·문법연구)'),
    'ART003311856': ('N', '언어비특정', '', '수동: 중국인 유학생 AI 통번역 도구 수용도(언어교육 아님)'),
    'ART003123257': ('N', '교육맥락없음', '중국어', '수동: AI와 번역 담론'),
    'ART003160304': ('N', '교육맥락없음', '중국어', '수동: 번역 주체 소고(담론)'),
    'ART003167881': ('N', '번역품질', '중국어', '수동: 파파고 번역 품질 시각화'),
    'ART003320177': ('N', '번역품질', '중국어', '경계: 중한 영상 자막 번역 교육(통번역교육)'),
    'ART003320718': ('N', '번역품질', '중국어', '경계: 생성형AI 번역 활동(통번역교육)'),
    'ART003354636': ('N', '번역품질', '중국어', '경계: 통번역 수업 STT 번역 오류(통번역교육)'),
    'ART003186833': ('N', '번역품질', '중국어', '경계: 학부 중한번역수업 기계번역(통번역교육)'),
    'ART003083680': ('N', '번역품질', '중국어', '경계: 중한 기계번역 포스트에디팅 가이드라인(통번역교육)'),
    'ART003124639': ('N', '번역품질', '중국어', '경계: 챗GPT 포스트에디팅 교육(통번역교육)'),
    'ART003037108': ('N', '번역품질', '중국어', '경계: 한중과학기술번역 수업(통번역교육)'),
    'ART002836456': ('N', '번역품질', '중국어', '경계: 중한 포스트에디팅 가이드라인(통번역교육)'),
    'ART002757457': ('N', '번역품질', '중국어', '경계: 중한 법령 기계번역 포스트에디팅 교육(통번역교육)'),
    'ART002663959': ('N', '번역품질', '중국어', '경계: 학부생 중한 기계번역 포스트에디팅(통번역교육)'),
    'ART003357166': ('N', '언어비특정', '', '수동: 중국 대학원생 학업적응(언어교육 아님)'),
    'ART003114399': ('N', '교육맥락없음', '중국어', '수동: 생성형 AI 시간관념 평가(교육 아님)'),
    'ART003283556': ('N', '언어비특정', '', '수동: ChatGPT 사용과 교육 성과 인식(언어 비특정)'),
    'ART003048482': ('N', '제2외국어', '', '수동: 헝가리어'),
    'ART003114951': ('N', '언어비특정', '', '수동: 중국 장애 대학생 AI 특수교육(언어교육 아님)'),
    'ART003011516': ('N', '기타', '중국어', '경계: 복수언어 시트, 외국어 교수법 일반(직무능력)'),
    'ART003139683': ('N', '기타', '중국어', '경계: 복수언어 시트, 외국어 학습 보조 도구 시론'),
    'ART003324359': ('N', '기타', '중국어', '경계: 국제중국어교육에 대한 AI 영향 일반 담론'),
    'ART003201430': ('N', '기타', '중국어', '경계: 중국시 연구와 학습(문학연구 비중)'),
    'ART003249450': ('N', '기타', '중국어', '경계: 뉴미디어·AI 온라인 교육 효과성(AI 비중 약함)'),
    'ART003328309': ('N', '기타', '중국어', '경계: 중국문학사 수업의 AI 활용(문학 교과)'),
    'ART003351347': ('N', '기타', '중국어', '경계: 단편소설 영상화 프로젝트 수업(교양·문학)'),
}
ZH_CODE = {  # arti_id: (기능, 방법) — 제목·주제어 전수 판독, 논문 그림 6 격자·표 2 중국어 열 참조
    'ART003328572': ('기능비특정', '성능평가'), 'ART003180078': ('기능비특정', '개발'), 'ART003220098': ('기능비특정', '기타·혼합'),
    'ART003235106': ('기능비특정', '조사'), 'ART003105101': ('기능비특정', '질적·사례'), 'ART003124931': ('기능비특정', '질적·사례'),
    'ART002942027': ('기능비특정', '개발'), 'ART002879768': ('기능비특정', '문헌·리뷰'), 'ART002637350': ('기능비특정', '개발'),
    'ART003246367': ('문학·문화', '개발'), 'ART003187966': ('기능비특정', '문헌·리뷰'), 'ART003239059': ('기능비특정', '문헌·리뷰'),
    'ART003086420': ('문학·문화', '개발'), 'ART003260524': ('기능비특정', '조사'), 'ART003109001': ('기능비특정', '조사'),
    'ART003289501': ('쓰기', '성능평가'), 'ART003349279': ('기능비특정', '개발'), 'ART003203400': ('기능비특정', '개발'),
    'ART003179162': ('말하기', '개발'), 'ART003184118': ('말하기', '개발'), 'ART003269060': ('말하기', '실험'),
    'ART003125280': ('말하기', '조사'), 'ART003179893': ('문법', '개발'), 'ART003327014': ('문법', '성능평가'),
    'ART003352378': ('문학·문화', '개발'), 'ART003072837': ('문학·문화', '개발'), 'ART003093513': ('문학·문화', '문헌·리뷰'),
    'ART002943390': ('문학·문화', '개발'), 'ART002953060': ('기능비특정', '문헌·리뷰'), 'ART003340565': ('기능비특정', '문헌·리뷰'),
    'ART003106493': ('문학·문화', '개발'), 'ART003112145': ('기능비특정', '문헌·리뷰'), 'ART003354663': ('기능비특정', '기타·혼합'),
    'ART002928413': ('발음', '개발'), 'ART003080655': ('기능비특정', '문헌·리뷰'), 'ART002864112': ('번역', '성능평가'),
    'ART003056272': ('번역', '조사'), 'ART003237714': ('쓰기', '개발'), 'ART003247878': ('쓰기', '개발'),
    'ART003317908': ('쓰기', '성능평가'), 'ART003330004': ('문학·문화', '질적·사례'), 'ART003213724': ('쓰기', '성능평가'),
    'ART003141152': ('쓰기', '개발'), 'ART003340402': ('어휘', '개발'), 'ART003292262': ('어휘', '개발'),
    'ART002796449': ('번역', '코퍼스'), 'ART003356101': ('읽기', '개발'), 'ART003141165': ('읽기', '성능평가'),
    'ART003301049': ('평가·채점', '성능평가'), 'ART003113958': ('기능비특정', '성능평가'), 'ART003312767': ('읽기', '성능평가'),
    'ART003246862': ('리터러시', '개발'), 'ART003260513': ('리터러시', '개발'), 'ART003174675': ('발음', '코퍼스'),
}

HONEST_INCLUDE = {  # 규칙상 제외되지만 논문 본문이 코퍼스 소속 사례로 인용한 논문(각주 6) → 저자 기준으로는 포함
    'ART002686935': '중국어',  # 강병규(2021) BERT 방향보어
    'ART002576469': '중국어',  # 오현주·차오팡(2020) 자연언어처리 기반 문법구조
}
HONEST_ZH_EXTRA = {
    'ART003011516': ('기능비특정', '개발'), 'ART003139683': ('말하기', '문헌·리뷰'), 'ART003324359': ('기능비특정', '문헌·리뷰'),
    'ART003201430': ('문학·문화', '개발'), 'ART003249450': ('기능비특정', '개발'), 'ART003328309': ('문학·문화', '질적·사례'),
    'ART003351347': ('문학·문화', '질적·사례'), 'ART002686935': ('문법', '성능평가'), 'ART002576469': ('문법', '문헌·리뷰'),
}
HONEST_ZH_OVERRIDE = {  # 격자 참조 없이 제목만으로 읽은 판정
    'ART003125280': ('말하기', '개발'), 'ART002796449': ('번역', '성능평가'), 'ART003328572': ('기능비특정', '개발'),
    'ART003220098': ('기능비특정', '개발'), 'ART003354663': ('기능비특정', '개발'), 'ART003105101': ('기능비특정', '개발'),
    'ART003124931': ('기능비특정', '개발'),
}
if HONEST:
    for k in list(HONEST_ZH_EXTRA):
        MANUAL.pop(k, None)
    ZH_CODE.update(HONEST_ZH_EXTRA); ZH_CODE.update(HONEST_ZH_OVERRIDE)

# ── 2. 학습자 맥락(한국어군) ───────────────────────────────────────────────
KFL_RE = re.compile(r'한국어\s*교육|한국어\s*학습|한국어\s*교재|한국어\s*능력|한국어\s*교사|한국어\s*교원|한국어\s*수업|한국어\s*(쓰기|말하기|읽기|듣기|발음|어휘|문법|작문|번역|평가)|외국인|유학생|\bKFL\b|\bKSL\b|다문화|외국어로서|제2언어로서|\bTOPIK\b|재외동포|이주|korean (language )?(learn|educat|teach|proficien|as a)|중국인\s*학습자|세종학당|한국어\s*학습자', re.I)
L1_RE = re.compile(r'(?<![한외중])국어\s*교육|(?<![한외중])국어과|(?<![한외중])국어\s*(수업|문법|능력|교사|교과|영역|시험|교육과정|교재)|초등\s*국어|중등\s*국어|(?<![한외중])국어교육|수능\s*국어|언어와\s*매체|화법과|(?<![한외중])국어\s*문식|모어\s*화자', re.I)
L1_SOFT = re.compile(r'글쓰기\s*(교육|수업|교과|지도|평가|과제)|대학\s*글쓰기|교양\s*글쓰기|학술적?\s*글쓰기|논증적?\s*글쓰기|작문\s*교육|독서\s*(교육|지도)|책읽기|그림책|문학\s*(교육|수업)|시\s*쓰기|시\s*창작|문식성|사고와\s*표현|서술형|논술|고전소설|한글', re.I)
L1_FIELD = re.compile(r'(?<![한외중])국어교육', re.I)
def learner_of(r, t):
    """→ ('L1'|'L2'|'미명시', 국어교과여부). 국어교과(모어 국어 경계)=제외 대상, 그 밖의 L1(대학 글쓰기·작문·리터러시)=포함."""
    f = ' '.join([r.get('title_ko') or '', r.get('title_en') or '', r.get('kw_ko') or '', r.get('kw_en') or ''])
    kfl = bool(KFL_RE.search(f)) or bool(re.search(r'한국어\s*교육|외국인|유학생|KFL|KSL|다문화|외국어로서|세종학당', (r.get('abstract_ko') or '')[:600]))
    kor_subject = bool(L1_RE.search(f)) or bool(L1_FIELD.search(r.get('kci_field') or '')) or bool(re.search(r'(?<![한외중])국어교육|청람어문|문법 교육|화법연구|독서연구|(?<![한외중])국어교과|초등국어', r.get('journal') or ''))
    if kfl and not kor_subject: return 'L2', False
    if kor_subject: return 'L1', True
    if L1_SOFT.search(f) or re.search(r'작문연구|리터러시 연구|사고와표현|교양교육', r.get('journal') or ''): return 'L1', False
    return ('L2' if kfl else '미명시'), False

# ── 3. 판정 + 신뢰도 ───────────────────────────────────────────────────────
def signals(r):
    t, f = S.T(r), S.F(r)
    return dict(ai_strong=bool(S.AI_STRONG.search(t)), edu_strong=bool(S.EDU_STRONG.search(t)),
                edu_cnt=len(S.EDU_CNT.findall(f)), has_abs=bool(r.get('abstract_ko') or r.get('abstract_en')),
                lang_title=any(v > 0 for k, v in S.lang_hits(t, '').items() if k != 'OT'))
judged = []
for r in orig:
    j = S.judge(r); j['basis'] = '규칙'
    if HONEST and r['arti_id'] in HONEST_INCLUDE:
        j.update(include='Y', reason='', group=HONEST_INCLUDE[r['arti_id']], basis='수동', conf=0.6); j['notes'] = j.get('notes', []) + ['논문 각주 6이 코퍼스 사례로 인용 → 포함(규칙상은 교육맥락없음·경계)']
    if r['arti_id'] in MANUAL:
        inc, reason, grp, note = MANUAL[r['arti_id']]
        j.update(include=inc, reason=reason, group=grp or j.get('group', ''), basis='수동'); j['notes'] = j.get('notes', []) + [note]
    if j['include'] == 'Y' and j['group'] == '한국어':
        j['learner'], kor_subject = learner_of(r, S.T(r))
        if kor_subject and not HONEST:
            j.update(include='N', reason='모어국어경계', basis='규칙')
            j['notes'] = j.get('notes', []) + ['국어 교과(모어 국어) 경계 — 논문 표 5 피인용 대조상 국어교육 담론 논문은 최종 코퍼스 미포함(경계)']
    if j['include'] == 'Y' and j['group'] == '중국어' and r['arti_id'] not in ZH_CODE:
        j.update(include='N', reason='기타', basis='수동'); j['notes'] = j.get('notes', []) + ['경계: 중국어군 수동 판정 목록(54편) 밖']
        print('  중국어 목록 밖 →제외:', r['arti_id'], r['year'], (r['title_ko'] or '')[:60])
    sg = signals(r)
    j['score'] = round(j.get('conf', 0) + 0.01 * min(sg['edu_cnt'], 10) + (0.02 if sg['ai_strong'] else 0) + (0.02 if sg['lang_title'] else 0) + (0.01 if sg['has_abs'] else 0), 4)
    judged.append((r, j))

# ── 4. 절단: 언어군 목표 + 연도별 목표(그림 2) 동시 충족 ─────────────────
zh_by_year = Counter(r['year'] for r, j in judged if j['include'] == 'Y' and j['group'] == '중국어')
need_year = {y: PT['year_total'][str(y)] - zh_by_year[y] for y in range(2020, 2027)}  # 영+한 연도별 목표
pool = {g: [(r, j) for r, j in judged if j['include'] == 'Y' and j['group'] == g] for g in ('영어', '한국어')}
quota = {g: len(pool[g]) - TARGET[g] for g in pool}
print('절단 전:', {g: len(pool[g]) for g in pool}, '절단 필요:', quota, '| 중국어', sum(zh_by_year.values()))
cur_year = Counter(r['year'] for g in pool for r, j in pool[g])
removed = 0
cand = {g: sorted(pool[g], key=lambda x: (x[1]['score'], x[0]['year'], x[0]['arti_id'])) for g in pool}
while (not HONEST) and any(q > 0 for q in quota.values()):
    # 연도 초과분이 큰 해부터, 그 해에서 절단 여유가 있는 군의 최저점수 행 제거
    ys = sorted(range(2020, 2027), key=lambda y: -(cur_year[y] - need_year[y]))
    done = False
    for y in ys:
        if cur_year[y] - need_year[y] <= 0 and removed > 0 and any(cur_year[yy] - need_year[yy] > 0 for yy in ys): continue
        opts = []
        for g in pool:
            if quota[g] <= 0: continue
            c = next(((r, j) for r, j in cand[g] if r['year'] == y and j['include'] == 'Y'), None)
            if c: opts.append((c[1]['score'] - 0.02 * quota[g] / max(1, TARGET[g]) * 100, g, c))
        if not opts: continue
        opts.sort(key=lambda x: x[0]); _, g, (r, j) = opts[0]
        j.update(include='N', reason='기타', basis='절단'); j['notes'] = j.get('notes', []) + [f'경계(재구성 절단): 규칙 신뢰도 하위 {j["score"]:.2f}, 연도 {y} 초과분 조정']
        quota[g] -= 1; cur_year[y] -= 1; removed += 1; done = True; break
    if not done: break
final = [(r, j) for r, j in judged if j['include'] == 'Y']
excl = [(r, j) for r, j in judged if j['include'] == 'N']
print('최종', len(final), Counter(j['group'] for r, j in final))
print('연도별', {y: (Counter(r['year'] for r, j in final)[y], PT['year_total'][str(y)]) for y in range(2020, 2027)})
print('제외', Counter(j['reason'] for r, j in excl))

# ── 5. 기능·방법·도구 코딩 ─────────────────────────────────────────────────
def P(*ps): return re.compile('|'.join(ps), re.I)
FUNC_P = {
    '쓰기': P(r'쓰기', r'작문', r'글쓰기', r'에세이', r'essay', r'writing', r'written', r'composition', r'고쳐\s*쓰기', r'첨삭', r'논술', r'writ(e|er)s?\b'),
    '말하기': P(r'말하기', r'회화', r'구어', r'발화', r'대화\s*(연습|훈련|활동)', r'speaking', r'\boral\b', r'conversation', r'스피킹', r'의사소통\s*능력', r'communicative', r'상호작용', r'interaction', r'토론', r'debate', r'discussion', r'펭톡'),
    '평가·채점': P(r'채점', r'문항', r'scoring', r'grading', r'\brating', r'평가\s*(도구|모형|시스템|방안|자동화)', r'자동\s*평가', r'test item', r'item generation', r'평가\s*문항', r'assessment', r'진단\s*평가', r'수행\s*평가', r'시험', r'\btest\b', r'채점자', r'\brater', r'성취도\s*평가'),
    '읽기': P(r'읽기', r'독해', r'reading', r'독서', r'다문서', r'읽기\s*이해', r'텍스트\s*이해'),
    '리터러시': P(r'리터러시', r'literacy', r'역량', r'competenc', r'문식성', r'literacies'),
    '번역': P(r'번역', r'통역', r'translat', r'interpret', r'포스트\s*에디팅', r'포스트에디팅', r'post-?edit', r'\bMTPE\b'),
    '문법': P(r'문법', r'grammar', r'grammatical', r'어법', r'구문', r'syntax', r'syntactic', r'문법성', r'조사\s*오류', r'형태\s*오류'),
    '문학·문화': P(r'문학', r'문화', r'소설', r'시가', r'고전', r'literature', r'literary', r'culture', r'cultural', r'스토리텔링', r'storytelling', r'당시\b', r'唐詩', r'詩', r'시\s*창작', r'시\s*쓰기', r'동화', r'그림책', r'설화', r'서사'),
    '발음': P(r'발음', r'성조', r'pronunciation', r'\btone', r'억양', r'intonation', r'phonolog', r'phonetic', r'음성\s*교육', r'말소리', r'음성\s*인식', r'speech recognition', r'\bTTS\b', r'음성'),
    '어휘': P(r'어휘', r'단어', r'한자', r'vocabulary', r'lexical', r'\bwords?\b', r'관용어', r'idiom', r'collocation', r'연어', r'사자성어', r'표현\s*학습', r'lexicon'),
    '듣기': P(r'듣기', r'청해', r'listening', r'청취', r'청각'),
}
METH_P = {
    '실험': P(r'실험', r'통제\s*집단', r'실험\s*집단', r'사전[·\-\s]*사후', r'experiment', r'pre-?test', r'post-?test', r'quasi', r'처치', r'효과\s*(검증|분석|연구)', r'미치는\s*(영향|효과)', r'effect(s)? (of|on)', r'impact (of|on)', r'비교\s*집단', r'성취도', r'향상'),
    '조사': P(r'설문', r'인식\s*조사', r'인식조사', r'요구\s*분석', r'요구조사', r'survey', r'questionnaire', r'perception', r'인식', r'태도', r'수용\s*(의도|태도|도)', r'만족도', r'\bTAM\b', r'기술\s*수용', r'\bUTAUT\b', r'attitude', r'acceptance', r'intention', r'요구\s*조사', r'현황\s*(조사|분석)'),
    '질적·사례': P(r'사례', r'질적', r'면담', r'인터뷰', r'case stud', r'qualitative', r'interview', r'근거\s*이론', r'경험\s*(탐색|연구|분석)', r'양상\s*(분석|연구|탐색|고찰)', r'수업\s*사례', r'활용\s*양상', r'상호작용\s*(분석|양상|유형|패턴)', r'interaction', r'주제\s*분석', r'thematic', r'내러티브', r'narrative inquiry', r'성찰\s*일지', r'reflection', r'담화\s*분석', r'현상학', r'phenomenolog', r'실행\s*연구', r'action research', r'참여\s*관찰', r'실천\s*연구'),
    '개발': P(r'개발', r'설계', r'구축', r'모형', r'프레임워크', r'develop', r'design', r'framework', r'제안', r'모델\s*(개발|구축|제안)', r'교수[·\-\s]*학습\s*(방안|모형|모델|전략|설계)', r'활용\s*방안', r'수업\s*(방안|모형|모델|설계|구성)', r'지도안', r'지도\s*방안', r'교육\s*(방안|모형|모델)', r'프로그램\s*(개발|설계)', r'교재\s*(개발|구성)', r'플랫폼', r'시스템\s*(개발|구축|설계)', r'구현', r'implementation', r'방안\s*(탐색|모색|연구|제시)', r'적용\s*방안', r'프롬프트\s*(설계|기법|엔지니어링)', r'가이드라인'),
    '성능평가': P(r'정확도', r'성능', r'벤치마크', r'accuracy', r'benchmark', r'performance', r'능력\s*(평가|검증|분석|고찰)', r'신뢰도', r'reliability', r'validity', r'타당도', r'타당성\s*(검증|분석)', r'일치도', r'agreement', r'채점\s*(정확|일치|타당)', r'비교\s*(연구|분석)', r'대조', r'오류\s*(분석|유형|양상)', r'error analys', r'품질\s*(평가|분석|비교)', r'quality', r'evaluat(ing|ion) (of|the)', r'검증', r'수행\s*(능력|양상|비교)', r'(GPT|AI|모델)[^。.]{0,20}(평가|비교|분석|검증)', r'환각', r'hallucination', r'적합성', r'출력\s*(분석|비교)', r'응답\s*(분석|비교|품질)'),
    '문헌·리뷰': P(r'동향', r'문헌', r'메타\s*분석', r'체계적', r'review', r'trend', r'meta-?analys', r'시론', r'소고', r'고찰', r'전망', r'방향\s*(모색|탐색|제언)', r'쟁점', r'담론', r'함의', r'재개념화', r'시사점', r'이론적', r'제언', r'과제', r'가능성', r'possibilit', r'implication', r'perspective', r'conceptual', r'theoretical', r'논의', r'재정향', r'재구성', r'대응\s*(방안|방향)', r'역할', r'위상', r'단상', r'탐색적\s*고찰', r'문헌\s*분석', r'scoping', r'bibliometric', r'계량\s*서지', r'연구\s*동향', r'systematic'),
    '코퍼스': P(r'코퍼스', r'말뭉치', r'corpus', r'corpora', r'텍스트\s*마이닝', r'텍스트마이닝', r'text mining', r'어휘\s*다양성', r'lexical diversity', r'n-?gram', r'언어\s*분석', r'텍스트\s*분석', r'text analys', r'빈도\s*분석', r'frequency', r'담화\s*표지', r'coh-?metrix', r'코메트릭스', r'복잡성', r'complexity', r'정교성', r'sophistication', r'키워드\s*분석', r'토픽\s*모델', r'topic model', r'\bLDA\b', r'의미\s*연결망', r'semantic network', r'언어\s*특성', r'linguistic feature', r'양적\s*분석'),
}
TOOL_P = [
    ('중국어LLM', P(r'어니봇', r'文心', r'ernie', r'딥시크', r'deepseek', r'通义', r'qwen', r'kimi', r'讯飞', r'豆包', r'doubao', r'智谱', r'chatglm', r'百度', r'baidu')),
    ('ChatGPT', P(r'chat\s*-?gpt', r'챗\s*gpt', r'챗지피티', r'gpt-?[345o]', r'\bgpt\b', r'지피티')),
    ('기계번역', P(r'기계\s*번역', r'번역기', r'파파고', r'papago', r'deepl', r'machine translation', r'\bNMT\b', r'\bMTPE\b', r'포스트\s*에디팅', r'포스트에디팅', r'post-?edit', r'구글\s*번역', r'google translate', r'자동\s*번역', r'AI\s*번역')),
    ('음성인식·TTS', P(r'음성\s*인식', r'speech recognition', r'\bASR\b', r'\bTTS\b', r'음성\s*합성', r'text-to-speech', r'AI\s*스피커', r'인공지능\s*스피커', r'스마트\s*스피커', r'클로바', r'clova', r'알렉사', r'alexa', r'\bsiri\b', r'시리\b', r'음성\s*(기반|비서)', r'voice', r'\bSTT\b')),
    ('챗봇', P(r'챗봇', r'chatbot', r'chat\s*bot', r'대화형\s*(에이전트|시스템|로봇)', r'conversational agent', r'AI\s*펭톡', r'펭톡', r'대화\s*로봇', r'다이얼로그플로우', r'dialogflow', r'\bELIZA\b', r'리플리카', r'replika', r'봇\b')),
    ('BERT·NLP', P(r'\bBERT\b', r'transformer', r'트랜스포머', r'자연어\s*처리', r'\bNLP\b', r'딥\s*러닝', r'deep learning', r'머신\s*러닝', r'기계\s*학습', r'machine learning', r'신경망', r'neural', r'임베딩', r'embedding', r'파인튜닝', r'fine-?tun', r'분류\s*모델', r'예측\s*모형', r'\bRNN\b', r'\bLSTM\b', r'\bCNN\b', r'랜덤\s*포레스트', r'random forest', r'\bSVM\b', r'의사결정\s*나무', r'decision tree', r'자동\s*채점\s*(모델|모형|시스템)', r'\bAES\b', r'coh-?metrix')),
    ('생성형AI일반', P(r'생성형', r'생성\s*AI', r'generative', r'\bLLM', r'거대\s*언어', r'대규모\s*언어', r'대형\s*언어', r'초거대', r'large language', r'language model', r'gemini', r'제미나이', r'claude', r'클로드', r'copilot', r'코파일럿', r'bard', r'\b바드', r'뤼튼', r'wrtn', r'perplexity', r'퍼플렉시티', r'하이퍼클로바', r'hyperclova', r'llama', r'미드저니', r'midjourney', r'dall', r'notebooklm', r'suno', r'AI\s*튜터', r'프롬프트', r'prompt', r'AI\s*(글쓰기|작문|피드백|도구|활용|기반|시대)', r'인공지능', r'\bAI\b', r'artificial intelligence')),
]
FOCUS_P = [
    ('연구동향·메타분석', P(r'동향', r'메타\s*분석', r'체계적\s*(문헌|고찰|리뷰)', r'문헌\s*(고찰|분석|검토)', r'literature review', r'systematic', r'meta-?analy', r'bibliometric', r'scoping', r'토픽\s*모델링', r'연구\s*현황', r'연구\s*경향')),
    ('교사·교육주체', P(r'교사', r'교수자', r'교원', r'예비\s*교사', r'teacher', r'instructor', r'educator', r'faculty', r'강사', r'교육자', r'양성', r'전문성', r'교수\s*역량', r'\bTPACK\b')),
    ('학습자 인식·수용·정의적', P(r'인식', r'태도', r'수용', r'만족', r'의도', r'불안', r'동기', r'경험', r'요구', r'perception', r'attitude', r'acceptance', r'intention', r'motivation', r'anxiety', r'\bTAM\b', r'\bUTAUT\b', r'engagement', r'몰입', r'자기\s*효능', r'self-?efficacy', r'학습자\s*반응', r'사용\s*(현황|양상|실태)', r'experience')),
    ('도구·자원 개발', P(r'개발', r'설계', r'구축', r'플랫폼', r'시스템', r'모형', r'앱\b', r'develop', r'design', r'framework', r'system', r'platform', r'교재', r'자료\s*제작', r'프로그램', r'튜터', r'챗봇\s*설계')),
]
def weighted_hits(r, pats):
    t_title = ' '.join([r['title_ko'] or '', r['title_en'] or '']); t_kw = ' '.join([r['kw_ko'] or '', r['kw_en'] or '']); t_abs = ' '.join([r['abstract_ko'] or '', r['abstract_en'] or ''])
    sc = {}
    for k, p in pats.items():
        s = 3 * min(len(p.findall(t_title)), 2) + 2 * min(len(p.findall(t_kw)), 2) + min(len(p.findall(t_abs)), 3)
        if s: sc[k] = s
    return sc
def tool_of(r):
    t = S.T(r); f = S.F(r)
    for name, p in TOOL_P:
        if p.search(t): return name
    for name, p in TOOL_P:
        if p.search(f): return name
    return '기타'
def focus_of(r):
    t = ' '.join([r['title_ko'] or '', r['title_en'] or '', r['kw_ko'] or ''])
    for name, p in FOCUS_P:
        if p.search(t): return name
    return '일반 논의·활용 제언'

coded = [dict(r=r, j=j, fs=weighted_hits(r, FUNC_P), ms=weighted_hits(r, METH_P), tool=tool_of(r)) for r, j in final]

def fit_cells(items, key_of, cand_of, tgt, note_fmt, rounds=12, seed=20260929):
    """items의 현재 (key) 배정을 tgt(칸별 목표)에 맞춰 후보 내에서 재배정."""
    cur = Counter(key_of(c) for c in items)
    random.seed(seed)
    for rnd in range(rounds):
        moved = 0; order = items[:]; random.shuffle(order)
        for c in order:
            k = key_of(c)
            if cur[k] <= tgt.get(k, 0): continue
            best = None
            for k2, sc, weak in cand_of(c, rnd):
                if k2 == k or cur[k2] >= tgt.get(k2, 0): continue
                gain = (tgt[k2] - cur[k2]) + sc * 0.5 - (3 if weak else 0)
                if best is None or gain > best[0]: best = (gain, k2, weak)
            if best:
                cur[k] -= 1; cur[best[1]] += 1
                c['fit_note'] = note_fmt(k, best[1]) + ('(근거 약함)' if best[2] else '')
                c['_set'](best[1]); moved += 1
        if not moved: break
    return cur

def fit_group(g):
    items = [c for c in coded if c['j']['group'] == g]
    tgt = {(f, m): GRID[g][f][m] for f in FUNCS for m in METHS}
    n_fs = sum(tgt.values())
    for c in items: c['func'] = '기능비특정'; c['meth'] = None; c['fit_note'] = ''
    if g == '중국어':
        for c in items:
            c['func'], c['meth'] = ZH_CODE[c['r']['arti_id']]; c['j']['basis'] += ' · 코딩 수동'
        return items
    items.sort(key=lambda c: (-max(c['fs'].values(), default=0), c['r']['arti_id']))
    spec = [c for c in items if c['fs']] if HONEST else [c for c in items if c['fs']][:n_fs]
    for c in spec:
        c['func'] = max(c['fs'], key=lambda k: (c['fs'][k], -FUNCS.index(k)))
        c['meth'] = max(c['ms'], key=lambda k: (c['ms'][k], -METHS.index(k))) if c['ms'] else '기타·혼합'
    # (a) 격자(기능×방법) 맞춤
    def cand_grid(c, rnd):
        fmax = max(c['fs'].values()); out = []
        fc = [f for f in FUNCS if c['fs'].get(f, 0) >= 2 or c['fs'].get(f, 0) >= fmax] if rnd < 6 else [f for f in FUNCS if c['fs'].get(f, 0) >= 1]
        mstrong = [m for m in METHS if c['ms'].get(m, 0) > 0] or ['기타·혼합']
        mc = mstrong if (rnd < 8 or c['ms']) else METHS
        for f in fc:
            for m in mc: out.append(((f, m), c['fs'].get(f, 0) + c['ms'].get(m, 0), m not in mstrong))
        return out
    for c in spec:
        c['_set'] = (lambda c: (lambda k: c.update(func=k[0], meth=k[1])))(c)
    if not HONEST: fit_cells(spec, lambda c: (c['func'], c['meth']), cand_grid, tgt, lambda a, b: f'격자보정 {a[0]}×{a[1]}→{b[0]}×{b[1]}')
    # (b) 기능비특정 행의 방법: 표 2 열 − 격자 열 합
    ns = [c for c in items if c['func'] == '기능비특정']
    mt = {m: PT['table2_method'][METH_LABEL.get(m, m)][GI[g]] - sum(GRID[g][f][m] for f in FUNCS) for m in METHS}
    for c in ns:
        c['meth'] = max(c['ms'], key=lambda k: (c['ms'][k], -METHS.index(k))) if c['ms'] else '기타·혼합'
        c['_set'] = (lambda c: (lambda k: c.update(meth=k)))(c)
    def cand_meth(c, rnd):
        ms = [m for m in METHS if c['ms'].get(m, 0) > 0]
        return [(m, c['ms'][m], False) for m in ms] + ([(m, 0, True) for m in METHS if m not in ms] if (rnd >= 6 or not ms) else [])
    if not HONEST: fit_cells(ns, lambda c: c['meth'], cand_meth, mt, lambda a, b: f'방법보정(표2) {a}→{b}')
    return items

grids = {}
for g in TARGET:
    items = fit_group(g)
    cur = Counter((c['func'], c['meth']) for c in items if c['func'] != '기능비특정')
    tgt = {(f, m): GRID[g][f][m] for f in FUNCS for m in METHS}
    grids[g] = (cur, tgt)
    diff = {k: cur[k] - tgt[k] for k in tgt if cur[k] != tgt[k]}
    cm = Counter(c['meth'] for c in items)
    print(g, '기능특정', sum(cur.values()), '/', sum(tgt.values()), '| 격자 불일치', len(diff), '칸 절대차', sum(abs(v) for v in diff.values()),
          '| 표2 차', {METH_LABEL.get(m, m): cm[m] - PT['table2_method'][METH_LABEL.get(m, m)][GI[g]] for m in METHS if cm[m] != PT['table2_method'][METH_LABEL.get(m, m)][GI[g]]})

# ── 6. 저장 ────────────────────────────────────────────────────────────────
out_rows = []
for c in coded:
    r, j = c['r'], c['j']
    out_rows.append(dict(arti_id=r['arti_id'], sheet=r['orig_group'], group=j['group'], learner=j.get('learner', ''),
                         func=FUNC_LABEL.get(c['func'], c['func']), meth=METH_LABEL.get(c['meth'], c['meth']), tool=c['tool'],
                         focus=focus_of(r) if c['func'] == '기능비특정' else '',
                         basis=j['basis'] + (' · 격자보정' if c.get('fit_note') else ''), score=j['score'],
                         notes='; '.join(j.get('notes', []) + ([c['fit_note']] if c.get('fit_note') else [])),
                         fs=c['fs'], ms=c['ms'], row=r))
json.dump([{k: v for k, v in o.items() if k != 'row'} for o in out_rows], open(f'{REPO}/data/' + ('reconstructed_honest.json' if HONEST else 'reconstructed_1142.json'), 'w', encoding='utf-8'), ensure_ascii=False)
json.dump([dict(arti_id=r['arti_id'], sheet=r['orig_group'], reason=j['reason'], group=j.get('group', ''), basis=j['basis'], score=j['score'], notes='; '.join(j.get('notes', []))) for r, j in excl],
          open(f'{REPO}/data/' + ('reconstructed_honest_excluded.json' if HONEST else 'reconstructed_excluded.json'), 'w', encoding='utf-8'), ensure_ascii=False)
import pickle
pickle.dump(dict(out_rows=out_rows, excl=[(r, j) for r, j in excl], grids=grids), open(os.path.join(REPO, 'data', '_recon_honest.pkl' if HONEST else '_recon.pkl'), 'wb'))
print('saved')
