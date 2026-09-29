export const meta = {
  name: 'manuscript-edit-list',
  description: '원고 36쪽을 6구간으로 나눠 수정 항목(찾기 문자열·새 문장)을 뽑고 독립 검증',
  phases: [
    { title: 'Locate', detail: '구간별로 1,166편 기준 수정 항목 전수 추출' },
    { title: 'Verify', detail: '찾기 문자열 검사, 수치 재계산, 누락 탐색' },
  ],
}

const MS = 'C:\\Users\\user\\AppData\\Local\\Temp\\claude\\C--Users-user\\dc7faf3d-4217-45cf-857c-af864b52228e\\scratchpad\\ms'
const REPO = 'C:\\총보관\\학술지\\2026\\2026.07 교육공학학회 AI 중국어교육 연구의 현황과 공백\\KCI-corpus-recollection-2026'

const CHUNKS = [
  { key: 'c1', pages: [1, 2, 3, 36], desc: '국문 제요·주제어(1–2쪽), 1. 서론(3쪽), 영문 Abstract·Keywords(36쪽)' },
  { key: 'c2', pages: [4, 5, 6, 7, 8, 9], desc: '2. 이론적 배경, 3.1 연구 대상 및 자료 수집(각주 2·3 포함), 3.2(<표 1> 제외 기준), 3.3 분석 방법, κ 관련 서술' },
  { key: 'c3', pages: [10, 11, 12, 13, 14], desc: '4.1(<그림 1>·<그림 2>, 각주 6), 4.2 도입과 <표 2>·각주 9' },
  { key: 'c4', pages: [15, 16, 17, 18, 19], desc: '<그림 3>, 4.3 주제 확산(<표 3>·<그림 4>, 각주 10·11), 4.4 공저 네트워크(<표 4>·<그림 5>, 각주 12·13), 4.5 도입' },
  { key: 'c5', pages: [20, 21, 22, 23, 24, 25], desc: '4.5 인용(<표 5>~<표 8>, 각주 14 등), 5.1 연구 초점의 지형(<표 9>·<표 10>)' },
  { key: 'c6', pages: [26, 27, 28, 29, 30, 31, 32, 33, 34, 35], desc: '<그림 6>, <표 11>, <표 12>, 5.2, 5.3, 6. 결론, 참고문헌(33–35쪽)' },
]

const ITEM = {
  type: 'object',
  properties: {
    page: { type: 'integer' },
    section: { type: 'string' },
    kind: { type: 'string', enum: ['숫자교체', '서술재작성', '표교체', '그림교체', '삭제', '추가', '보류'] },
    find: { type: 'string' },
    find_end: { type: 'string' },
    find_check: { type: 'string' },
    original: { type: 'string' },
    replacement: { type: 'string' },
    basis: { type: 'string' },
    note: { type: 'string' },
  },
  required: ['page', 'section', 'kind', 'find', 'original', 'replacement', 'basis'],
}
const OUT = {
  type: 'object',
  properties: {
    items: { type: 'array', items: ITEM },
    unresolved: { type: 'array', items: { type: 'string' } },
    changes: { type: 'array', items: { type: 'string' } },
  },
  required: ['items', 'unresolved'],
}

const COMMON = `
## 과제 배경
논문 「AI 활용 중국어교육 연구의 현황과 공백: 영어·한국어교육과의 계량서지·네트워크 비교」(중국언어연구 J1_202600078)의 심사 후 수정이다.
원 코딩표가 유실되어 KCI Open API 후보 1,644편 전편의 초록을 다시 판정했고, 코퍼스가 바뀌었다.
- 제출본: 1,142편(영어 667, 한국어 421, 중국어 54)
- 확정: 1,166편(영어 711, 한국어 386, 중국어 69), 제외 478편
저자가 직접 한글(hwp)에서 고친다. 우리가 만드는 것은 "Ctrl+F로 찾을 문자열 + 바꿀 문장" 목록이다.

## 저자 결정(반드시 따른다)
- [AI+언어교육] 융합 연구만 대상. 국어 교과 담론형 제외(L1 실증연구는 유지), 대학 교양(글쓰기·읽기·토론) 제외, AI 디지털교과서 제외.
- 통번역 수업은 AI를 번역 교육에 적용했으면 포함. 문법·NLP는 교육적 적용이 있으면 포함. 자동채점·화법 평가 도구는 교양 맥락이어도 포함.
- 각주 6의 두 논문(강병규 2021, 오현주·차오팡 2020)은 코퍼스 밖이며, 각주 6은 "코퍼스 밖 선행연구 안내"로 고쳐 쓴다(대조표 3절 초안).
- κ(코더 간 일치도, 164편 표본 등)는 저자가 새로 계산한다. κ와 그 표본에 관한 수치·서술은 kind='보류', replacement='κ 재산출 후 기입'으로만 적고 값을 만들지 않는다.
- 목표 수치에 맞추지 않는다. 새 값은 반드시 아래 데이터에서 나와야 한다. 데이터로 정할 수 없으면 kind='보류'로 두고 무엇이 필요한지 적는다. 값을 지어내지 않는다.

## 입력 파일
- 원고 쪽별 텍스트(pdftotext -raw, 물리적 줄 유지, 각주·표 정확): ${MS}\\p01.txt … p36.txt (파일명 두 자리)
- 원고 전체: ${MS}\\hwp_rawmode.txt(-raw), ${MS}\\hwp.txt(기본 추출, 띄어쓰기 정확·줄바꿈 자리에 공백), ${MS}\\hwp_layout.txt
- 원고 PDF(그림·표 모양 확인용, Read 도구로 pages 지정해 볼 수 있음): ${REPO}\\manuscript\\J1_202600078.hwp.pdf (PDF 쪽수 = 한글 쪽수)
- 수치 대조표(이미 절별로 정리한 원문→수정, 초록·5.1 재작성 초안 포함): ${REPO}\\원고수정_수치대조표_1166_20260930.md — 단, 이 대조표는 누락이 있다고 가정하라.
- 분석 결과: ${REPO}\\analysis\\tables_4to8_1166_20260930.md/.json, rarefaction_1166_20260930.md/.json, keyword_diffusion_1166_20260930.md/.json, rejudge_summary_1166_20260930.md
- 확정 보고서: ${REPO}\\코퍼스확정_20260930.md, 판정 규칙: ${REPO}\\data\\rejudge\\CODING_GUIDE.md
- 원자료(재계산용): ${REPO}\\data\\rejudge\\merged_1166_20260930.json — 후보 1,644편 전체. include=='Y'가 확정 1,166편.
  필드: group(영어/한국어/중국어), year, func(쓰기·말하기·평가·채점·읽기·리터러시·역량·번역·문법·문학·문화·발음·어휘·듣기·기능비특정), meth(개발연구·조사연구·질적·사례·실험연구·문헌·리뷰·성능평가·코퍼스분석·기타·혼합), tool, focus, learner(L1/L2/''), n_authors, authors, cited, n_refs, reason(제외 사유), title_ko.
  Python에서 한글을 출력할 때는 sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8') 를 먼저 둔다.
- 찾기 문자열 검사기: python "${MS}\\check_keys.py" "문자열1" "문자열2" ... (결과 OK/WARN/FAIL, 출현 쪽)

## 파일 쓰기 제한
저장소(${REPO})와 논문 폴더의 파일은 절대 수정하지 않는다. 계산용 임시 파일은 ${MS}\\wf\\ 아래에만 만든다.

## 항목 작성 규칙
- 담당 쪽의 본문·각주·표·그림 캡션에서 코퍼스 변경으로 값이나 서술이 바뀌어야 하는 곳을 **전부** 찾는다. 편수, 비율, 순위, 배율, 연도별 수치, "단 1편"·"최다" 같은 비교 서술, 수집·판정 절차 서술(예: "검색어 커버리지 검증과 초록 재판정의 이중 필터링", "수동으로 직접 제외")까지 포함한다.
- 원칙은 최소 수정이다. 방향이 유지되면 숫자만 바꾼다(숫자교체). 새 데이터가 원문의 주장과 어긋나면 서술재작성으로 하고, 데이터가 보여 주는 것만 논문 문체(학술 문어체, "-였다/-이다")로 쓴다.
- find: 한글 Ctrl+F로 찾을 짧은 문자열(8–30자 권장). 반드시 한 물리적 줄 안에 있어야 하고(p??.txt의 한 줄 안), 원고 전체에서 유일해야 한다. check_keys.py로 확인해 OK인 것을 쓴다. WARN이면 note에 이유를 쓴다. 모든 find에 대해 검사기를 실제로 돌리고 판정을 find_check에 "OK"/"WARN" 식으로 적는다.
- find_end: 긴 단락·문장을 통째로 바꿀 때 범위 끝을 찾을 문자열(선택, 같은 규칙).
- original: 바꿀 원문 구절 전체(PDF 줄바꿈 공백은 제거해 hwp 원문처럼). 표는 원래 표를 행 단위로.
- replacement: 그대로 붙여 넣을 새 문장. 표교체는 새 표 전체를 파이프 마크다운 표로. 그림교체는 새 그림을 그릴 데이터 표와 바꿔야 할 캡션·범례. 삭제는 빈 문자열. 보류는 필요한 작업.
- basis: 새 값의 출처(대조표 절, 분석 파일과 키, 또는 merged json에서의 계산식).
- 한 문장에 숫자가 여러 개면 한 항목으로 묶어 문장 단위로 바꾸는 편이 저자에게 편하다.
- 대조표 9절의 신설·부록 권고는 해당 쪽에 넣을 자리가 있으면 kind='추가', note='권고(선택)'로 적는다.
`

function locatePrompt(c) {
  return `${COMMON}
## 너의 담당
담당 쪽: ${c.pages.join(', ')}쪽 — ${c.desc}
담당 쪽의 p??.txt를 처음부터 끝까지 읽고(각주 포함), 필요하면 PDF 해당 쪽을 Read로 보아 표·그림을 확인하라. 앞뒤 쪽은 문맥 확인용으로만 본다(항목은 담당 쪽에서 시작하는 것만).
대조표의 해당 절을 참고하되 대조표에 없는 수치·서술도 모두 찾아라. 새 값은 대조표 또는 분석 파일에서 가져오고, 없으면 merged json에서 직접 계산해 basis에 계산식을 적는다.
unresolved에는 데이터로 결정할 수 없거나 저자 판단이 필요한 점을 적는다.`
}

function verifyPrompt(c, loc) {
  return `${COMMON}
## 너의 역할: 독립 검증(적대적)
담당 쪽: ${c.pages.join(', ')}쪽 — ${c.desc}
다른 에이전트가 만든 수정 항목 목록이 아래에 있다. 틀렸다고 가정하고 반박을 시도하라.
1. 모든 find/find_end를 check_keys.py로 실제로 검사하라. FAIL이면 같은 구절 안에서 OK가 나오는 다른 문자열로 고친다. find_check에 결과를 적는다.
2. replacement의 모든 새 수치를 merged json(include=='Y') 또는 분석 파일에서 직접 다시 계산해 대조하라. 대조표 값도 믿지 말고 확인하라. 틀리면 고친다.
3. original이 원고 텍스트와 실제로 일치하는지(p??.txt) 확인하라. 원고에 없는 원문을 지어냈다면 고치거나 삭제한다.
4. replacement가 원고 문체에 맞고 문법적으로 자연스러운지, 옛 수치(1,142·667·421·54 등)가 남지 않았는지, 저자 결정(κ 보류, 각주 6, 교양·AIDT 제외 등)과 어긋나지 않는지 확인하라.
5. 담당 쪽을 다시 처음부터 읽어 빠진 항목(코퍼스 변경으로 바뀌어야 하는데 목록에 없는 수치·서술)을 찾아 추가하라.
최종 목록 전체(수정·추가 반영)를 items로 반환하고, changes에는 네가 바꾼 점을 항목별로 짧게 적어라(예: "p7 3.1 한국어 비율 36.9→33.1 누락 추가", "p14 find FAIL→교체").

## 검증 대상 목록(JSON)
${JSON.stringify(loc, null, 1)}`
}

const results = await pipeline(
  CHUNKS,
  c => agent(locatePrompt(c), { label: `locate:${c.key} p${c.pages[0]}-${c.pages[c.pages.length - 1]}`, phase: 'Locate', schema: OUT }),
  (loc, c) => loc ? agent(verifyPrompt(c, loc), { label: `verify:${c.key}`, phase: 'Verify', schema: OUT }).then(v => ({ chunk: c.key, pages: c.pages, located: loc, verified: v })) : { chunk: c.key, pages: c.pages, located: null, verified: null },
)
return results
