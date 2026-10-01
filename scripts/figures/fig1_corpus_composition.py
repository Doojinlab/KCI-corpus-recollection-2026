# -*- coding: utf-8 -*-
"""fig1_corpus_composition.py — <그림 1> 최종 코퍼스 언어군 구성(누적 가로 막대)을 확정 코퍼스로 다시 그린다.

원 그림(hwp BinData BIN0003, 1568×672)과 같은 크기·배치: 둥근 테두리 카드, 제목, 단위, 누적 가로 막대(막대 안 비율), 범례(편수).
색은 원 그림 계열을 유지하되 색각 이상 판별·대비 검사를 통과하도록 조정했다(파랑 #1859a3, 초록 #008a6a, 주황 #e35a00).
작은 중국어 막대의 비율은 막대 위에 본문 글자색으로 쓴다(색만으로 구별하지 않도록 범례에 편수를 함께 쓴다).
산출: figures/그림1_언어군구성_<DATE>.png
사용: python scripts/figures/fig1_corpus_composition.py [--date 1161_20261001]
"""
import json, os, sys
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
DATE = sys.argv[sys.argv.index('--date') + 1] if '--date' in sys.argv else '1161_20261001'
GROUPS = [('영어', '#1859a3'), ('한국어', '#008a6a'), ('중국어', '#e35a00')]
INK, MUTED, BORDER, SURFACE = '#111111', '#555555', '#d4d4d4', '#ffffff'
FONT = 'C:/Windows/Fonts/NotoSansKR-VF.ttf'


def font(size, weight='Bold'):
    try:
        f = ImageFont.truetype(FONT, size)
        f.set_variation_by_name(weight)
        return f
    except Exception:
        return ImageFont.truetype('C:/Windows/Fonts/malgunbd.ttf', size)


rows = json.load(open(f'{REPO}/data/rejudge/merged_{DATE}.json', encoding='utf-8'))
n = Counter(r['group'] for r in rows if r['include'] == 'Y')
total = sum(n[g] for g, _ in GROUPS)
pct = {g: round(n[g] / total * 100, 1) for g, _ in GROUPS}

W, H = 1568, 672
im = Image.new('RGB', (W, H), SURFACE)
d = ImageDraw.Draw(im)
d.rounded_rectangle((14, 18, W - 16, H - 36), radius=22, outline=BORDER, width=3, fill=SURFACE)

# 제목과 단위
d.text((57, 92), f'최종 코퍼스 {total:,}편의 언어군 구성', font=font(46), fill=INK)
d.text((W - 50, 104), '단위: 편(%)', font=font(30, 'Medium'), fill=MUTED, anchor='ra')

# 누적 가로 막대
x0, x1, y0, y1, gap = 57, W - 57, 218, 422, 3
span = x1 - x0
x = x0
segs = []
for i, (g, color) in enumerate(GROUPS):
    w = span * n[g] / total
    right = x1 if i == len(GROUPS) - 1 else x + w - gap
    segs.append((g, color, x, right))
    x += w
for i, (g, color, a, b) in enumerate(segs):
    if i == 0:
        d.rounded_rectangle((a, y0, b, y1), radius=14, fill=color)
        d.rectangle((b - 16, y0, b, y1), fill=color)          # 오른쪽 모서리는 각지게
    elif i == len(segs) - 1:
        d.rounded_rectangle((a, y0, b, y1), radius=14, fill=color)
        d.rectangle((a, y0, a + 16, y1), fill=color)          # 왼쪽 모서리는 각지게
    else:
        d.rectangle((a, y0, b, y1), fill=color)
    label = f'{pct[g]:.1f}%'
    if b - a > 200:                                           # 넓은 막대는 안쪽에 흰 글자
        d.text(((a + b) / 2, (y0 + y1) / 2), label, font=font(56), fill='#ffffff', anchor='mm')
    else:                                                     # 좁은 막대는 위쪽에 본문 글자색
        d.text((b, y0 - 14), label, font=font(44), fill=INK, anchor='rd')

# 범례(편수 병기)
lx = [57, 585, 1115]
for (g, color), xx in zip(GROUPS, lx):
    d.rounded_rectangle((xx, 497, xx + 62, 559), radius=8, fill=color)
    d.text((xx + 90, 528), f'{g} {n[g]}편', font=font(44), fill=INK, anchor='lm')

out_dir = f'{REPO}/figures'
os.makedirs(out_dir, exist_ok=True)
out = f'{out_dir}/그림1_언어군구성_{DATE}.png'
im.save(out, dpi=(300, 300))
print('saved', out, {g: (n[g], pct[g]) for g, _ in GROUPS}, 'total', total)
