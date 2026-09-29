# -*- coding: utf-8 -*-
"""build_editlist.py — 원고 수정 교체 목록(원고수정_교체목록_1166_20260930.md) 생성.

입력: analysis/manuscript_edit_items_raw_1166_20260930.json (6구간 추출·독립 검증 워크플로 결과,
      워크플로 스크립트는 scripts/manuscript/workflow_edit_list.js)
      manuscript/text/ (extract_text.py 결과)
처리: 구간 경계 중복 4개 제거, 쪽·본문 위치 순 번호, 찾기 문자열 재검사, 저자 결정 10가지 머리말
출력: 원고수정_교체목록_1166_20260930.md, analysis/manuscript_edit_items_1166_20260930.json
사용: python scripts/manuscript/build_editlist.py
"""
import io, os, re, sys, json
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_keys import check
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
items = json.load(open(os.path.join(REPO, 'analysis', 'manuscript_edit_items_raw_1166_20260930.json'), encoding='utf-8'))
for i, it in enumerate(items): it['_old'] = i
# 중복 정리(같은 자리를 두 구간이 다룸): 쪽 담당 구간 항목을 남긴다
it20 = items[20]
it20['note'] = (it20.get('note') or '') + (' 각주 5(Landis–Koch 구간 설명)는 일반 정의라 바꾸지 않되, 새 κ에 0.61 미만인 축이 있으면 '
                                           '본문 판정 문장과 함께 고친다. "해당 결과는 분류 기준의 일관성을 뒷받침한다" 문장은 새 κ를 보고 유지 여부를 정한다.')
DROP = {19, 21, 23, 24}
items = [it for it in items if it['_old'] not in DROP]
pages = io.open(os.path.join(REPO, 'manuscript', 'text', 'hwp_rawmode.txt'), encoding='utf-8').read().split('\f')
ns = lambda s: re.sub(r'\s+', '', s or '')


def pos(it):
    p = ns(pages[it['page'] - 1]); k = ns(it['find'])
    i = p.find(k)
    return i if i >= 0 else 10 ** 6


items.sort(key=lambda it: (it['page'], pos(it)))
NO = {it['_old']: n for n, it in enumerate(items, 1)}


def refs(*olds): return ', '.join(f'#{NO[o]}' for o in olds if o in NO)
def fix(s): return (s or '').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def bq(s):
    s = fix(s).strip('\n')
    return '\n'.join('> ' + l if l.strip() else '>' for l in s.split('\n')) if s else '> (비움)'


kinds = Counter(it['kind'] for it in items)
O = []
A = O.append
A('# 원고 수정 교체 목록 — J1_202600078_수정본.hwp (확정 코퍼스 1,166편)\n')
A('논문 폴더의 `J1_202600078_수정본.hwp`를 한글에서 직접 고칠 때 쓰는 목록이다. 쪽수는 한글 화면의 쪽수다(hwp에서 내보낸 PDF와 같다). '
  '원고 36쪽 전체를 쪽 단위로 훑어 코퍼스 변경(1,142편 → 1,166편)으로 바뀌어야 하는 곳을 모두 모았다.\n')
A(f'**항목 {len(items)}개**: ' + ' · '.join(f'{k} {v}' for k, v in kinds.most_common()) + '\n')
A('## 사용법\n')
A('- **찾기**: Ctrl+F에 그대로 넣는다. 원고 전체에서 한 번만 나오는 문자열로 골랐고 기계로 검사했다. **끝**이 있으면 찾기부터 끝까지를 통째로 바꾼다.')
A('- **각주 항목(⚑)**: PDF에서 각주 텍스트를 한 가지 방식으로만 뽑을 수 있어 띄어쓰기를 두 번 대조하지 못했다. 찾기가 안 잡히면 숫자 부분만으로 찾거나, '
  '한글 찾기가 각주를 검색하지 않으면 해당 쪽 각주 번호로 가서 고친다.')
A('- **종류**: 숫자교체(값만 바꿈) · 서술재작성(문장을 바꿈) · 표교체(셀 값을 새 표대로) · 그림교체(이미지를 새로 그려 넣음) · '
  '추가(새 문장·절, 대부분 권고) · 보류(κ처럼 저자가 계산·확인한 뒤 기입) · 삭제')
A('- 각 항목 제목 앞의 ☐는 진행 표시용이다. 모든 새 값은 `data/rejudge/merged_1166_20260930.json`과 `analysis/*_1166_20260930.*`에서 계산했고, 항목마다 근거를 적었다.\n')

A('## 먼저 정할 것 — 여러 항목에 걸친 저자 결정\n')
A('아래 결정에 따라 해당 항목을 넣거나 빼야 한다. 권장안을 함께 적었다.\n')
DEC = [
    ('1. 재판정의 주체를 사실대로 밝히기 (가장 중요, 심사위원 2-3)',
     '이번 1,644편 초록 판정은 연구자가 정한 판정 기준(`data/rejudge/CODING_GUIDE.md`, L1·R3 규칙)에 따라 **AI 에이전트가 1차 판정**했고, '
     '경계 사례 438편의 저자 검수는 아직 하지 않았다. 목록의 수정문은 "초록을 검토하여 판정하였다"처럼 주체를 적지 않았다. 원고에는 실제 절차를 적어야 한다. '
     '예: "1,644편의 초록은 연구자가 정한 판정 기준(부록 A)에 따라 대규모 언어모델을 보조 도구로 사용해 1차 판정하였고, 경계 사례 438편은 연구자가 검토하여 확정하였다." '
     '둘째 문장은 저자가 실제로 경계 사례를 검수한 뒤에만 쓸 수 있다. 학술지의 생성형 AI 사용 고지 규정도 확인한다.',
     refs(0, 9, 15, 113, 121)),
    ('2. 규모 통제 분석(희박화·초기하 확률)을 방법에 넣을지',
     '초록·4.2·4.3·5.1·5.2·결론의 새 서술은 "같은 편수를 무작위 추출해 비교"한 결과에 기대고 있다. 그런데 원문 3.3은 "유의수준을 설정한 가설검정은 실시하지 않았다"고 적고 있다. '
     '**권장: 3.4를 신설하고 3.3 끝 문장을 고친다.** 이 확률들은 모집단 추론이 아니라 규모 효과를 점검하는 보조 지표로 규정한다. '
     '넣지 않기로 하면 초록·5.1의 확률 서술(P<0.0001 등)을 모두 빼고 "규모 효과로 설명된다"는 서술만 남긴다.',
     refs(25, 26, 2, 123, 49, 55, 59, 96, 97, 105, 107, 114, 117)),
    ('3. 검색어 커버리지의 정의 (각주 4)',
     '제출본의 커버리지 값(91.7·90.2·77.6%)은 정의와 스크립트가 남아 있지 않아 재현되지 않는다. 수정문은 원고의 AI 시드 어휘 5개를 확정 코퍼스의 제목·주제어·초록에 '
     '적용한 값(영어 88.7%, 한국어 79.8%, 중국어 85.5%)으로 바꿨다. 이 정의를 채택할지 정한다. '
     '재현율 검증(보충 검색 신규 2,785편 판정, 중국어교육 학술지 목차 대조)은 아직 하지 않았으므로 재현율 수치는 쓸 수 없다. 1단계 검색어 서술은 7월 질의 목록을 확인한 뒤 보완한다.',
     refs(15, 8)),
    ('4. 표 5를 11편으로 할지 (10위 동률)',
     '재조회 피인용에서 60회가 3편 동률(9위)이다. **권장: 동률을 모두 싣고 공동 순위로 적는다(11편, 표 제목은 "상위 10위").** '
     '10편만 싣겠다면 동률을 깨는 규칙을 정해야 하고, 그에 따라 본문 편수와 참고문헌(한송희 2023)도 바뀐다. '
     '또 7/1 조회보다 늦게 조회했는데도 일부 논문의 피인용이 줄었다(예: 69→60회). KCI에서 한 번 확인한다.',
     refs(67, 68, 69, 119, 120)),
    ('5. 초록 분량',
     '재작성으로 국문 제요가 약 250자, 영문 Abstract가 약 80단어 길어진다. 분량 제한이 있으면 주제 출현 시차 문장부터 빼고, 그다음 방법 구성 확률 문장을 줄인다.',
     refs(2, 3, 123, 124)),
    ('6. 5.3의 정기인 외(2024) 사례',
     '이 논문은 후보 1,644편 밖에 있고 대학 교양 국어 글쓰기 연구로, 이번에 제외한 범주다. 비교군 선행좌표의 사례로 계속 쓸지, 단서를 붙일지, 코퍼스 안의 사례로 바꿀지 정한다.',
     refs(109)),
    ('7. 표 형식',
     '표 2는 새 값의 내림차순으로 정렬해 두었다(원래 순서를 지킬 때의 값은 항목 참고란). 표 9·10은 칸 값만 바꾸도록 원래 행 순서를 유지했다. '
     '표 1의 "AI 비중심 연구" 행은 선정 기준과 겹치므로 넣을지 고른다. 표 8은 한글이 없는 문헌을 한 열로 묶으면 중국어군이 42.1%로 한국어군보다 높아져 '
     '원문과 방향이 반대가 되므로, 영문과 중문을 나눈 안을 냈다(열을 늘리지 않으려면 영문 한 열 + 중문은 각주).',
     refs(43, 80, 84, 12, 74)),
    ('8. 주제군 이름 "정책·에듀테크(AI 디지털교과서)"',
     'AI 디지털교과서 연구는 제외했으므로 이 주제군은 확정 코퍼스에서 주로 "에듀테크" 키워드로 잡힌다. 괄호를 빼고 "정책·에듀테크"로 부르는 것을 권한다(표 3·그림 4).',
     refs(56, 57)),
    ('9. κ (보류)',
     '코더 간 일치도는 저자가 1,166편 기준으로 새로 계산한다. 관련 항목은 "κ 재산출 후 기입"으로만 표시했다. '
     '새 코딩에서 학습자 맥락(L1/L2)은 한국어군에만 있어, 학습자 맥락 κ는 한국어군 표본으로만 산출할 수 있다.',
     refs(20, 86, 116)),
    ('10. 경계 판정의 영향',
     '중국어군 69편 중 15편, 실험연구 4편 중 1편, 구축·평가형 34편 중 7편이 경계(boundary) 판정이다. '
     '저자 경계 검수에서 판정이 바뀌면 초록의 4편·49.3%·69.6%·5.9%와 희박화·확률 값을 다시 계산해야 한다.',
     ''),
]
for t, body, r in DEC:
    A(f'**{t}**  \n{body}' + (f'  \n관련 항목: {r}' if r else '') + '\n')

A('**코퍼스 변경과 무관한 원고 오기 (선택)** — 목록 작성 중 눈에 띈 것이다.\n')
A(f'- 11쪽 <그림 1> 캡션 "최총 코퍼스" → "최종 코퍼스" (#{NO[33]}에 포함)')
A(f'- 17쪽 <그림 4> 캡션이 <그림 3> 캡션("언어군별 실험연구 및 …")을 그대로 복사했다 (#{NO[57]})')
A('- 18쪽 본문 "동명이인에 따른 식별 오류 가능성을 없앴다"가 각주 12의 "동명이인을 완화하였다"와 어긋난다 → "줄였다" 권장')
A('- 24–25쪽 각주 17·18의 표 번호(<표 9>/<표 10>) 지칭이 표 구성과 맞지 않는다')
A('- 32쪽 "코머 간 일치도" → "코더 간 일치도"\n')
A('**이번에 함께 바로잡은 것 (저장소)** — 수치 대조표의 4.3 공유 키워드 수는 20개 개념 동의어 통합을 빠뜨려 73·341·109·94로 나왔었다. '
  '원고가 설명한 방법대로 통합하면 **41·168·61·52**다(시차 중앙값은 그대로 1년). 표 5는 10위 동률을 임의로 끊었던 것을 공동 순위로 고쳤다. '
  '`코퍼스확정_20260930.md`에 남아 있던 1,177편 단계의 값(제외 467편 등)도 확정값으로 고쳤다.\n')
fig = [it for it in items if it['kind'] == '그림교체']


def short(s): return re.sub(r'^\d\.\d\s*', '', s)


A(f'**그림 교체 {len(fig)}개**: ' + ', '.join(f'#{NO[it["_old"]]} {short(it["section"])}' for it in fig) +
  '. hwp에 이미지로 들어가 있어 새 데이터로 다시 그려 넣어야 한다. 항목마다 그릴 데이터를 적었다.\n')

A('## 쪽별 항목 수\n')
cp = Counter(it['page'] for it in items)
ps = sorted(cp)
A('| 쪽 | ' + ' | '.join(str(p) for p in ps) + ' |')
A('|---|' + '---|' * len(ps))
A('| 항목 | ' + ' | '.join(str(cp[p]) for p in ps) + ' |\n')

warn = 0
cur = None
for n, it in enumerate(items, 1):
    if it['page'] != cur:
        cur = it['page']
        A(f'\n---\n\n## {cur}쪽\n')
    flag = ''
    if check(it['find'])['verdict'] != 'OK':
        flag = ' ⚑'; warn += 1
    A(f'### ☐ {n}. {it["section"]} — {it["kind"]}\n')
    line = f'- **찾기**: `{fix(it["find"])}`{flag}'
    if it.get('find_end'):
        line += f'  \n  **끝**: `{fix(it["find_end"])}`'
    A(line)
    A('- **원문**\n\n' + bq(it['original'] or '(없음 — 새로 넣음)') + '\n')
    A('- **수정**\n\n' + bq(it['replacement']) + '\n')
    A(f'- 근거: {fix(it["basis"])}')
    if it.get('note'):
        A(f'- 참고: {fix(it["note"])}')
    A('')
A('\n---\n\n## 이 목록을 만든 방법\n')
A('1. hwp에서 내보낸 PDF(`manuscript/J1_202600078.hwp.pdf`)를 `pdftotext -raw`로 쪽별 추출했다(각주·표 행 순서가 정확한 방식).')
A('2. 원고를 6구간으로 나눠, 구간마다 한 에이전트가 수정 항목을 전수 추출하고 다른 에이전트가 독립 검증했다(찾기 문자열 검사, 새 수치를 확정 데이터에서 재계산, 누락 탐색).')
A('3. 모든 찾기 문자열을 세 가지 추출본에 대조해 원고 전체에서 유일함을 기계로 확인했다. 새 수치 가운데 대조표·분석 파일에 없는 값(8개 항목)은 확정 데이터에서 다시 계산해 일치를 확인했다.')
A('4. 구간 경계에서 겹친 항목 4개를 정리했다.')
out = '\n'.join(O)
print(len(items), 'items; footnote-warn', warn, 'chars', len(out))
json.dump([dict({k: v for k, v in it.items() if not k.startswith('_')}, no=n) for n, it in enumerate(items, 1)],
          open(os.path.join(REPO, 'analysis', 'manuscript_edit_items_1166_20260930.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
io.open(os.path.join(REPO, '원고수정_교체목록_1166_20260930.md'), 'w', encoding='utf-8', newline='\n').write(out)
