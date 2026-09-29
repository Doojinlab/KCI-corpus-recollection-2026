# -*- coding: utf-8 -*-
"""numaudit.py — 교체 목록 수정문의 숫자 가운데 대조표·분석 파일에 없는 값을 찾는다.

여기서 나온 숫자는 에이전트가 새로 계산한 값이므로 merged_1166 json에서 따로 재계산해 확인한다
(2026-09-30 점검: 8개 항목의 값을 모두 재계산해 일치 확인).
사용: python scripts/manuscript/numaudit.py
"""
import io, os, re, sys, json, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
R = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
src = [os.path.join(R, '원고수정_수치대조표_1166_20260930.md'), os.path.join(R, 'analysis', 'rejudge_summary_1166_20260930.md')]
src += [f for f in glob.glob(os.path.join(R, 'analysis', '*1166_20260930.*')) if 'manuscript_edit' not in os.path.basename(f)]
known = ''.join(io.open(f, encoding='utf-8').read() for f in src)
NUM = re.compile(r'\d[\d,]*(?:\.\d+)?')
norm = lambda t: t.replace(',', '')
K = set()
for k in {norm(m) for m in NUM.findall(known)}:
    K.add(k)
    try:
        x = float(k)
        for nd in (0, 1, 2):
            K.add(f'{x:.{nd}f}')   # 반올림 표기 허용
    except ValueError:
        pass
items = json.load(open(os.path.join(R, 'analysis', 'manuscript_edit_items_1166_20260930.json'), encoding='utf-8'))
tot = 0
for it in items:
    if it['kind'] == '보류':
        continue
    old = {norm(m) for m in NUM.findall(it.get('original', ''))}
    unk = sorted({x for x in (norm(m) for m in NUM.findall(it.get('replacement', '')))
                  if x not in K and x not in old and not re.fullmatch(r'(19|20)\d\d|\d', x)})
    if unk:
        tot += 1
        print(f'#{it["no"]} p{it["page"]} {it["section"]} ({it["kind"]}): {unk}')
print('items with numbers not in sheet/analysis files:', tot)
