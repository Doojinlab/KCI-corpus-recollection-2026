# -*- coding: utf-8 -*-
"""수정 항목이 덮지 못한 숫자 찾기(누락 점검).
사용: python scripts/manuscript/sweep.py analysis/manuscript_edit_items_1166_20260930.json
원고 1–32·36쪽(참고문헌 제외)의 숫자 토큰마다 그 줄이 어떤 항목의 original(공백 제거)에 포함되는지 본다."""
import io, os, re, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
D = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'manuscript', 'text'))
pages = io.open(os.path.join(D, 'hwp_rawmode.txt'), encoding='utf-8').read().split('\f')
items = json.load(open(sys.argv[1], encoding='utf-8'))
ns = lambda s: re.sub(r'\s+', '', s)
origs = [(it['page'], ns(it.get('original', '')) + ns(it.get('find', ''))) for it in items]
NUM = re.compile(r'(?<![\w.])\d[\d,]*(?:\.\d+)?(?:%|편|칸|명|개|회|배|년|위|년차)?')
YEAR = re.compile(r'^(19|20)\d\d(년)?$')
unc = []
for pi, p in enumerate(pages, 1):
    if pi in (33, 34, 35) or not p.strip():
        continue
    for line in p.split('\n'):
        toks = [m.group(0) for m in NUM.finditer(line)]
        toks = [t for t in toks if not YEAR.match(t) and not re.fullmatch(r'\d{1,2}', t)]
        if not toks:
            continue
        L = ns(line)
        # 줄의 일부(숫자 주변 12자)가 어떤 original에 들어 있으면 덮인 것으로 본다
        cov = []
        for t in toks:
            i = L.find(ns(t)); frag = L[max(0, i - 6): i + len(ns(t)) + 6]
            cov.append(any(frag in o for _, o in origs) or any(ns(t) in o and abs(pg - pi) <= 1 for pg, o in origs if len(ns(t)) >= 4))
        if not all(cov):
            unc.append((pi, [t for t, c in zip(toks, cov) if not c], line.strip()[:110]))
for pi, t, l in unc:
    print(f'p{pi:02d} {t} | {l}')
print('uncovered lines:', len(unc))
