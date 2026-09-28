# -*- coding: utf-8 -*-
"""심사위원 2 요구 재분석: 격자 점유율의 규모 효과 통제.

입력: grid_1142.json — 제출본 그림 6(언어기능 11 × 연구방법 8)의 언어군별 칸 편수.
출력: (1) 영어·한국어군에서 n편 무작위 재추출 시 기대 점유 칸수 분포와 중국어군 실측(24칸)의 위치
      (2) 초기하 확률: 36편 중 실험연구 1편 이하 / 개발·성능평가 26편 이상
      (3) 선도군 축적 임계값에 따른 확산대기·구조공백 민감도
"""
import json, os, random, statistics as st
from math import comb
from collections import Counter

random.seed(20260924)
HERE = os.path.dirname(os.path.abspath(__file__))
grid = json.load(open(os.path.join(HERE, 'grid_1142.json'), encoding='utf-8'))
rows = list(grid['영어'].keys()); cols = list(grid['영어'][rows[0]].keys())


def cells(p):
    out = []
    for r in rows:
        for c in cols:
            out += [(r, c)] * grid[p][r][c]
    return out


def rarefy(p, n, reps=10000):
    pool = cells(p); res = []; thick = []
    for _ in range(reps):
        s = random.sample(pool, n); k = len(set(s)); res.append(k); thick.append(n / k)
    res.sort()
    return dict(mean=round(st.mean(res), 2), sd=round(st.pstdev(res), 2), p2_5=res[int(0.025 * reps)],
                p50=res[reps // 2], p97_5=res[int(0.975 * reps)], P_le_24=round(sum(1 for k in res if k <= 24) / reps, 4),
                thick_mean=round(st.mean(thick), 2))


def hyper_cdf(K, N, n, k):
    return sum(comb(K, i) * comb(N - K, n - i) for i in range(0, k + 1)) / comb(N, n)


zh = cells('중국어')
print('중국어군 실측: n=%d, 점유 %d칸, 칸당 %.2f편' % (len(zh), len(set(zh)), len(zh) / len(set(zh))))
print('\n[1] 희박화 (1만 회)')
for p in ['영어', '한국어']:
    for n in [36, 39, 45, 54]:
        print(' ', p, n, rarefy(p, n))

print('\n[2] 초기하 검정 (36편 추출)')
for p in ['영어', '한국어']:
    N = len(cells(p))
    K_exp = sum(grid[p][r]['실험'] for r in rows)
    K_build = sum(grid[p][r]['개발'] + grid[p][r]['성능평가'] for r in rows)
    print('  %s N=%d 실험 %d(%.1f%%) 기대 %.1f P(실험<=1)=%.4f | 개발+성능 %d(%.1f%%) 기대 %.1f P(>=26)=%.4f' % (
        p, N, K_exp, 100 * K_exp / N, 36 * K_exp / N, hyper_cdf(K_exp, N, 36, 1),
        K_build, 100 * K_build / N, 36 * K_build / N, 1 - hyper_cdf(K_build, N, 36, 25)))
print('  중국어 실측: 실험 %d, 개발+성능 %d' % (sum(grid['중국어'][r]['실험'] for r in rows),
                                            sum(grid['중국어'][r]['개발'] + grid['중국어'][r]['성능평가'] for r in rows)))

print('\n[3] 공백 유형 (중국어 <=1편 좌표 기준)')
gap = [(r, c, grid['영어'][r][c] + grid['한국어'][r][c], grid['중국어'][r][c]) for r in rows for c in cols if grid['중국어'][r][c] <= 1]
empty = [(r, c) for r in rows for c in cols if grid['영어'][r][c] + grid['한국어'][r][c] + grid['중국어'][r][c] == 0]
print('  공백 %d칸, 세 군 모두 0편(구조공백) %d칸' % (len(gap), len(empty)), Counter(r for r, c in empty), Counter(c for r, c in empty))
for th in [5, 10, 15, 20]:
    w = sum(1 for x in gap if x[2] >= th)
    print('  선도군 임계값 %2d편 → 확산대기 %d, 나머지 %d' % (th, w, len(gap) - w))
w10 = [x for x in gap if x[2] >= 10]
print('  확산대기(10편) 선도군 합계 %d편, 나머지 공백 선도군 합계 %d편' % (sum(x[2] for x in w10), sum(x[2] for x in gap if x[2] < 10)))
