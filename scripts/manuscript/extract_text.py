# -*- coding: utf-8 -*-
"""extract_text.py — 제출본 원고 PDF에서 텍스트를 뽑아 manuscript/text/에 둔다.

hwp에서 내보낸 PDF(manuscript/J1_202600078.hwp.pdf, PDF 쪽수 = 한글 쪽수)를 pdftotext 세 방식으로 추출한다.
  hwp_rawmode.txt  -raw     물리적 줄 유지, 각주·표 행 순서가 정확(좁은 간격에서 띄어쓰기 누락 가능)
  hwp.txt          기본     띄어쓰기 정확, 줄바꿈 자리에 공백 삽입, 각주는 글자가 뒤섞임
  hwp_layout.txt   -layout  물리적 줄·띄어쓰기 유지, 표·각주는 깨짐
  p01.txt … p36.txt         -raw 추출을 쪽별로 나눈 것
pdftotext는 Git for Windows(mingw64/bin)에 들어 있다. 사용: python scripts/manuscript/extract_text.py
"""
import io, os, subprocess, sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PDF = os.path.join(REPO, 'manuscript', 'J1_202600078.hwp.pdf')
OUT = os.path.join(REPO, 'manuscript', 'text')
os.makedirs(OUT, exist_ok=True)
for flag, name in (('-raw', 'hwp_rawmode.txt'), (None, 'hwp.txt'), ('-layout', 'hwp_layout.txt')):
    cmd = ['pdftotext', '-enc', 'UTF-8'] + ([flag] if flag else []) + [PDF, os.path.join(OUT, name)]
    subprocess.run(cmd, check=True)
pages = io.open(os.path.join(OUT, 'hwp_rawmode.txt'), encoding='utf-8').read().split('\f')
n = 0
for i, p in enumerate(pages, 1):
    if p.strip():
        io.open(os.path.join(OUT, f'p{i:02d}.txt'), 'w', encoding='utf-8', newline='\n').write(p)
        n += 1
print(f'{n} pages -> {OUT}')
