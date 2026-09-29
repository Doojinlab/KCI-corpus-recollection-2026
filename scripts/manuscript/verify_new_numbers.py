# -*- coding: utf-8 -*-
"""verify_new_numbers.py — numaudit.py가 찾은 8개 항목(대조표에 없던 새 수치)을 확정 데이터에서 재계산.

2026-09-30 결과: 모두 교체 목록의 값과 일치.
  #10 1차 수집 범주별 편수(87·409·974·151·23)   #19 AI 시드 어휘 커버리지(88.7·79.8·85.5%, 미보유 168편)
  #33 2020–2022년 185편의 도구 구성              #41 개발+조사+질적·사례 602편(51.6%)
  #43 시기별 방법 비중(실험 16.2→16.9, 성능 15.7→12.8, 조사+질적 22.7→33.9)
  #72 참고문헌 확보 논문 932편, 참고문헌 29,341건
사용: python scripts/manuscript/verify_new_numbers.py
"""
import json, io, os, sys, re
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
A = json.load(open(os.path.join(REPO, 'data', 'rejudge', 'merged_1166_20260930.json'), encoding='utf-8'))
print('1차 수집 범주', Counter(r['sheet'] for r in A), len(A))
d = [r for r in A if r['include'] == 'Y']
e = [r for r in d if r['year'] <= 2022]; l = [r for r in d if r['year'] >= 2023]
print('2020–2022', len(e), Counter(r['tool'] for r in e).most_common())
print('  BERT·NLP 기능', Counter(r['func'] for r in e if r['tool'] == 'BERT·NLP'))
for nm, s in (('2020–2022', e), ('2023–2026', l)):
    c = Counter(r['meth'] for r in s); n = len(s)
    print(nm, n, '실험', c['실험연구'], round(100 * c['실험연구'] / n, 1), '성능', c['성능평가'], round(100 * c['성능평가'] / n, 1),
          '조사+질적', c['조사연구'] + c['질적·사례'], round(100 * (c['조사연구'] + c['질적·사례']) / n, 1))
c = Counter(r['meth'] for r in d)
k = c['개발연구'] + c['조사연구'] + c['질적·사례']
print('개발+조사+질적', k, round(100 * k / len(d), 1))
rf = [r for r in d if (r['n_refs'] or 0) > 0]
print('참고문헌 확보', len(rf), Counter(r['group'] for r in rf), sum(r['n_refs'] for r in rf))
pat = re.compile(r'(?<![A-Za-z])AI(?![A-Za-z])')
pat2 = re.compile(r'인공\s*지능|챗\s*봇|생성형\s*AI|chat\s*-?gpt|챗\s*gpt|챗\s*지피티', re.I)


def hit(r):
    t = ' '.join(str(r.get(k) or '') for k in ('title_ko', 'title_en', 'kw_ko', 'kw_en', 'abstract_ko', 'abstract_en'))
    return bool(pat.search(t) or pat2.search(t))


for G in ('영어', '한국어', '중국어'):
    s = [r for r in d if r['group'] == G]; h = sum(hit(r) for r in s)
    print('커버리지', G, h, len(s), round(100 * h / len(s), 1))
miss = [r for r in d if not hit(r)]
print('시드 미보유', len(miss), Counter(r['tool'] for r in miss).most_common())
