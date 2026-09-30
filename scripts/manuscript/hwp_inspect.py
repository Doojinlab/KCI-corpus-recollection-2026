# -*- coding: utf-8 -*-
"""hwp_inspect.py — HWP 5.0 파일을 읽기 전용으로 열어 구역별 각주 모양과 각주 위치를 보여 준다(외부 패키지 없음).

각주 번호가 원하는 모양(첫 쪽 저자 표기 ＊, 본문 1) 2) …)으로 나오는지, 구역 나누기가 남아 있는지 확인할 때 쓴다.
사용: python scripts/manuscript/hwp_inspect.py manuscript/수정원고.hwp
"""
import io, struct, sys, zlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def cfb_streams(path):
    d = open(path, 'rb').read()
    assert d[:8] == bytes.fromhex('D0CF11E0A1B11AE1'), 'OLE 파일이 아님'
    ss = 1 << struct.unpack_from('<H', d, 0x1E)[0]
    mss = 1 << struct.unpack_from('<H', d, 0x20)[0]
    n_fat, dir0 = struct.unpack_from('<II', d, 0x2C)
    cutoff, mfat0, n_mfat, difat0, n_difat = struct.unpack_from('<IIIII', d, 0x38)
    sec = lambda i: d[512 + i * ss: 512 + (i + 1) * ss]
    difat = list(struct.unpack_from('<109I', d, 0x4C))
    nxt = difat0
    for _ in range(n_difat):
        s = sec(nxt); difat += list(struct.unpack_from(f'<{ss // 4 - 1}I', s)); nxt = struct.unpack_from('<I', s, ss - 4)[0]
    fat = []
    for i in difat[:n_fat]:
        fat += list(struct.unpack_from(f'<{ss // 4}I', sec(i)))

    def chain(start, table, getter):
        out, i, seen = [], start, set()
        while i < 0xFFFFFFFA and i not in seen:
            seen.add(i); out.append(getter(i)); i = table[i]
        return b''.join(out)
    dirdata = chain(dir0, fat, sec)
    ents = []
    for k in range(len(dirdata) // 128):
        e = dirdata[k * 128:(k + 1) * 128]
        nl = struct.unpack_from('<H', e, 64)[0]
        name = e[:max(nl - 2, 0)].decode('utf-16le', 'replace')
        typ = e[66]; l, r, c = struct.unpack_from('<III', e, 68)
        start, size = struct.unpack_from('<II', e, 116)
        ents.append(dict(name=name, type=typ, l=l, r=r, c=c, start=start, size=size))
    root = ents[0]
    ministream = chain(root['start'], fat, sec) if root['start'] < 0xFFFFFFFA else b''
    mfat = []
    if n_mfat:
        mfd = chain(mfat0, fat, sec); mfat = list(struct.unpack_from(f'<{len(mfd) // 4}I', mfd))
    msec = lambda i: ministream[i * mss:(i + 1) * mss]

    def read(e):
        raw = chain(e['start'], mfat, msec) if e['size'] < cutoff else chain(e['start'], fat, sec)
        return raw[:e['size']]
    paths = {}

    def walk(i, prefix):
        if i >= len(ents) or i == 0xFFFFFFFF: return
        e = ents[i]
        walk(e['l'], prefix); walk(e['r'], prefix)
        p = prefix + e['name']
        if e['type'] == 2: paths[p] = e
        elif e['type'] == 1: walk(e['c'], p + '/')
    walk(root['c'], '')
    return paths, read


def records(buf):
    i = 0
    while i + 4 <= len(buf):
        h = struct.unpack_from('<I', buf, i)[0]; i += 4
        tag, lvl, size = h & 0x3FF, (h >> 10) & 0x3FF, (h >> 20) & 0xFFF
        if size == 0xFFF:
            size = struct.unpack_from('<I', buf, i)[0]; i += 4
        yield tag, lvl, buf[i:i + size]; i += size


EXT = {1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23}
INL = {4, 5, 6, 7, 8, 9, 19, 20}


def para_text(b):
    out, i, n = [], 0, len(b) // 2
    while i < n:
        c = struct.unpack_from('<H', b, i * 2)[0]
        if c in EXT or c in INL:
            out.append('{%d}' % c if c in EXT else ''); i += 8
        elif c < 32:
            out.append('\n' if c in (10, 13) else ''); i += 1
        else:
            out.append(chr(c)); i += 1
    return ''.join(out)


NUMFMT = {0: '1,2,3', 1: '①②③', 2: 'I,II,III', 3: 'i,ii,iii', 4: 'A,B,C', 5: 'a,b,c', 6: 'Ⓐ,Ⓑ', 7: 'ⓐ,ⓑ', 8: '가,나,다', 9: '㉮,㉯',
          10: 'ㄱ,ㄴ,ㄷ', 11: '㉠,㉡', 12: '일,이,삼', 13: '一,二,三', 14: '一二三(원)', 0x80: '4가지 문자 반복(*, **, …)', 0x81: '사용자 지정 문자 반복'}
NUMBERING = {0: '앞 구역에 이어서', 1: '현재 구역부터 새로 시작', 2: '쪽마다 새로 시작'}

path = sys.argv[1]
streams, read = cfb_streams(path)
hdr = read(streams['FileHeader'])
compressed = struct.unpack_from('<I', hdr, 36)[0] & 1
secs = sorted([p for p in streams if p.startswith('BodyText/Section')], key=lambda p: int(p[len('BodyText/Section'):]))
print('구역 수:', len(secs), '| 압축:', bool(compressed))
for sp in secs:
    buf = read(streams[sp])
    if compressed:
        buf = zlib.decompress(buf, -15)
    recs = list(records(buf))
    fshape = [r for r in recs if r[0] == 74]
    if fshape:
        b = fshape[0][2]
        attr = struct.unpack_from('<I', b, 0)[0]
        user, pre, suf = (chr(x) if x else '' for x in struct.unpack_from('<3H', b, 4))
        start = struct.unpack_from('<H', b, 10)[0]
        print(f'\n[{sp}] 각주 모양: 번호 모양={NUMFMT.get(attr & 0xFF, attr & 0xFF)}, 사용자 기호={user!r}, 앞 장식={pre!r}, 뒤 장식={suf!r}, '
              f'시작 번호={start}, 번호 매기기={NUMBERING.get((attr >> 10) & 3)}, 위첨자={(attr >> 13) & 1}')
    # 각주 컨트롤과 그 앞뒤 본문
    texts, fn_count = [], 0
    for k, (tag, lvl, data) in enumerate(recs):
        if tag == 67 and lvl == 1:
            texts.append(para_text(data))
        if tag == 71 and data[:4][::-1] == b'fn  ':
            fn_count += 1
            body = ''
            for t2, l2, d2 in recs[k + 1:k + 8]:
                if t2 == 67:
                    body = para_text(d2).strip(); break
            if fn_count <= 3 or '소속' in body:
                print(f'   각주 #{fn_count}: {body[:60]}')
    new_no = [r for r in recs if r[0] == 71 and r[2][:4][::-1] == b'nwno']
    print(f'   이 구역의 각주 수: {fn_count}, 새 번호로 시작 컨트롤: {len(new_no)}')
    full = ''.join(texts)
    for key in ('소속 및 직위', '＊', '1. 서론'):
        i = full.find(key)
        if i >= 0:
            print(f'   본문에서 "{key}" 위치: …{full[max(0, i - 30):i + 30]!r}…')
