# -*- coding: utf-8 -*-
"""check_keys.py — 한글 Ctrl+F로 찾을 문자열이 원고에서 유일하게 잡히는지 검사.

사용: python scripts/manuscript/check_keys.py "문자열1" "문자열2" ...
      python scripts/manuscript/check_keys.py --json analysis/manuscript_edit_items_1166_20260930.json
전제: scripts/manuscript/extract_text.py로 만든 manuscript/text/의 세 추출본
  raw  = pdftotext -raw (물리적 줄 유지, 각주·표 정확, 좁은 간격에서 띄어쓰기 누락 가능)
  dflt = pdftotext 기본 (띄어쓰기 정확, 줄바꿈 자리에 공백 삽입, 각주는 깨짐)
  lay  = pdftotext -layout (물리적 줄·띄어쓰기 유지, 표·각주는 깨짐)
  uniq = 공백을 모두 지운 원고 전체에서의 출현 횟수(1이어야 유일)
OK  : 줄바꿈 없음, uniq==1, raw/dflt/lay 중 2곳 이상에서 그대로 발견
WARN: uniq==1이나 1곳에서만 발견(대개 각주 — 띄어쓰기 확인 필요)
FAIL: uniq!=1 또는 어디서도 그대로 발견되지 않음
"""
import io, os, re, sys, json

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
T = os.path.join(REPO, 'manuscript', 'text')
rd = lambda n: io.open(os.path.join(T, n), encoding='utf-8').read()
raw, dflt, lay = rd('hwp_rawmode.txt'), rd('hwp.txt'), rd('hwp_layout.txt')
pages = raw.split('\f')
ns = lambda s: re.sub(r'\s+', '', s)
nsp = [ns(p) for p in pages]


def check(k):
    hits = [n for n, s in (('raw', raw), ('dflt', dflt), ('lay', lay)) if k in s]
    u = sum(p.count(ns(k)) for p in nsp)
    where = [i + 1 for i, p in enumerate(nsp) if ns(k) in p]
    if '\n' in k or u != 1 or not hits:
        v = 'FAIL'
    elif len(hits) >= 2:
        v = 'OK'
    else:
        v = 'WARN'
    return dict(key=k, verdict=v, found_in=hits, uniq=u, pages=where)


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    a = sys.argv[1:]
    keys = [it['find'] for it in json.load(open(a[1], encoding='utf-8'))] if a and a[0] == '--json' else a
    for k in keys:
        r = check(k)
        print(f"{r['verdict']:4} uniq={r['uniq']} pages={r['pages']} in={','.join(r['found_in']) or '-'} | {k}")
